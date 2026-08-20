# NTInet Operations Platform LNP v1.5.3

## Provider Draft Submission Fix

- Correctly reads nested `LnpOrderResponse.OrderId` and `ProcessingStatus` values.
- Treats the initial POST response as creation of a provider-side draft, not a completed submission.
- Sends a follow-up PUT with `ProcessingStatus=SUBMITTED` to enter the order into the active porting workflow.
- Recovers provider-side drafts created by v1.5.2 from submission history, avoiding unnecessary duplicate orders.
- Stores the actual provider order ID and current processing status locally.
- Redirects to the real port order detail page after submission.
