# TKT-4E Category Page Hotfix

Version 1.20.3 fixes an Internal Server Error on `/catalog/categories` caused by parent, child, and item relationships being accessed after the database session closed.

The category hierarchy and item counts are now eagerly loaded before rendering. This release adds no database migration; the expected database revision remains `20260807_15 (head)`.
