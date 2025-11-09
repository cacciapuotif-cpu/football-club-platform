# Pseudonymization Strategy

## Principles
- Replace direct identifiers (name, DOB) with tokens in operational datasets.
- Maintain separate secure mapping table (`token_vault`) accessible only to privacy admin role.

## Tokenization Flow
1. Generate UUIDv4 token per player.
2. Store mapping `{player_uuid ↔ token_uuid}` in encrypted table.
3. All analytics tables use token UUID; direct identifiers stored only in secure vault.

## Field-Level Masking
- Wellness data: if consent revoked → show token only, hide personal notes.
- Reports: for Viewer role, show initials or token.
- Audit logs: capture actor + reason, but mask subject PII.

## Key Management
- Token vault encryption keys stored in secrets manager.
- Rotate keys annually or on incident.

## Access Control
- Only DPO/privacy admin can re-identify.
- Access requests logged and approved via workflow.

