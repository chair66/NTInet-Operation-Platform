# NTInet Operations Platform LNP v1.4.1 — OnePort Carrier Group Hotfix

This hotfix corrects duplicate carrier detection in OnePort portability results. The nested `losingCarrier` object contains carrier metadata but no telephone-number list. It is no longer displayed as a separate carrier group when the same SPID is already represented by the complete portable-number group.
