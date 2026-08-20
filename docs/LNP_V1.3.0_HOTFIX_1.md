# LNP v1.3.0 Hotfix 1

This hotfix corrects multi-number portability input parsing.

Accepted examples:

```text
8038542105 8038540398 8038542292
8038542105, 8038540398, 8038542292
8038542105; 8038540398; 8038542292
8038542105
8038540398
8038542292
(803) 854-2105, (803) 854-0398
```

Each number is sent to Bandwidth as an individual E.164 value.
