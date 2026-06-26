# Hazardous Project List Recognition

This workflow is the first real Coze migration sample for the `szzg` collaboration track.

It recognizes a dangerous construction project checklist from an uploaded spreadsheet and returns the normalized JSON shape used by the original Coze workflow.

## Source

- Original platform: Coze
- Original workflow export: `source/coze_export/`
- Original Coze workflow name: `Automatic_creation_of_assignme`
- Original Coze description: `作业队伍自动创建`
- Business name in MyPrivateAgent: `危大工程清单识别`

The original Coze export name is preserved only as source evidence. The MyPrivateAgent workflow id is `hazardous_project_list_recognition`.

## Runtime Shape

The original Coze workflow is:

```text
start(upload_file)
  -> get_file_type
  -> LinkReaderPlugin
  -> LLM
  -> JSON deserialize
  -> end(output)
```

The MyPrivateAgent migration target is:

```text
file input
  -> document.file_type.detect
  -> spreadsheet.table.extract
  -> llm.classify
  -> json_schema.validate
  -> result envelope
```

## Status

Current status is `active`.

This workflow is registered as an asset and acceptance sample, and it is callable through the migration capability entrypoint.
