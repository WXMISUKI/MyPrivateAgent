const TARGET_SAMPLE_RATE = 16000
const TARGET_CHUNK_SAMPLES = 1600

function downsample(input, inputSampleRate, outputSampleRate) {
  if (inputSampleRate === outputSampleRate) {
    return input
  }
  const ratio = inputSampleRate / outputSampleRate
  const outputLength = Math.floor(input.length / ratio)
  const output = new Float32Array(outputLength)
  for (let i = 0; i < outputLength; i += 1) {
    const start = Math.floor(i * ratio)
    const end = Math.min(Math.floor((i + 1) * ratio), input.length)
    let sum = 0
    for (let j = start; j < end; j += 1) {
      sum += input[j]
    }
    output[i] = sum / Math.max(1, end - start)
  }
  return output
}

function floatToPcm16(input) {
  const buffer = new ArrayBuffer(input.length * 2)
  const view = new DataView(buffer)
  for (let i = 0; i < input.length; i += 1) {
    const sample = Math.max(-1, Math.min(1, input[i]))
    view.setInt16(i * 2, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true)
  }
  return buffer
}

class ManagedAsrProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super()
    this.targetSampleRate = options?.processorOptions?.targetSampleRate || TARGET_SAMPLE_RATE
    this.pendingChunks = []
    this.pendingLength = 0
  }

  process(inputs) {
    const input = inputs?.[0]?.[0]
    if (!input || input.length === 0) {
      return true
    }
    const chunk = downsample(input, sampleRate, this.targetSampleRate)
    this.pendingChunks.push(chunk)
    this.pendingLength += chunk.length
    if (this.pendingLength < TARGET_CHUNK_SAMPLES) {
      return true
    }

    const output = new Float32Array(this.pendingLength)
    let offset = 0
    for (const pendingChunk of this.pendingChunks) {
      output.set(pendingChunk, offset)
      offset += pendingChunk.length
    }
    this.pendingChunks = []
    this.pendingLength = 0

    const pcm = floatToPcm16(output)
    this.port.postMessage({ type: 'pcm', audio: pcm }, [pcm])
    return true
  }
}

registerProcessor('managed-asr-processor', ManagedAsrProcessor)
