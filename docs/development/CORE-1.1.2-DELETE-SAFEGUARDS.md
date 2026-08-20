# Core v1.1.2 – Admin Delete Safeguards

- Added a shared confirmation modal for deleting users and organizations.
- Administrators must type `delete` exactly before the Delete button is enabled.
- Added server-side confirmation checks so bypassing browser JavaScript cannot delete a record.
- Applied the same confirmation to bulk user deletion.
- Kept the NTInet staff organization protected from deletion and added an explanatory message.
- Deletions remain soft deletes and can be restored.
