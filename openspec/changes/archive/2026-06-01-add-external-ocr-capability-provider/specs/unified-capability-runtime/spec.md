## ADDED Requirements

### Requirement: External PaddleOCR provider registration

The backend SHALL register `document.ocr.extract` as an HTTP OCR capability when an external PaddleOCR provider is configured.

#### Scenario: OCR provider registration is enabled

- **GIVEN** `ENABLE_OCR_CAPABILITY_PROVIDER=true`
- **AND** `OCR_CAPABILITY_PROVIDER_BASE_URL` is configured
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** the response includes `document.ocr.extract`
- **AND** the capability has `kind = ocr`
- **AND** the capability has `transport = http`

#### Scenario: OCR provider is unavailable

- **GIVEN** the OCR provider is configured but unreachable
- **WHEN** a client requests capability health or heartbeat
- **THEN** the backend reports `status = unreachable`
- **AND** includes a machine-readable provider error
- **AND** the main server remains healthy

### Requirement: PaddleX OCR response normalization

The OCR capability SHALL map provider-neutral invoke requests to PaddleX serving and normalize PaddleX OCR responses into a compact provider-neutral envelope.

#### Scenario: OCR invocation succeeds

- **WHEN** a client invokes `POST /api/capabilities/document.ocr.extract/invoke`
- **THEN** the backend sends the file payload to PaddleX serving `POST /ocr`
- **AND** maps image media types to `fileType = 1`
- **AND** maps `application/pdf` to `fileType = 0`
- **AND** the response includes `text`, `pages`, `blocks`, and `raw` evidence

#### Scenario: OCR invocation input is missing

- **WHEN** a client invokes OCR without `file_base64`
- **THEN** the backend returns `ok = false`
- **AND** returns error code `OCR_INVALID_INPUT`
