---
name: Vershoudbakjes data rules
description: Editorial/data conventions and known-suspect records in the vershoudbakjes catalogue
---
- Usage info rule: None = unknown, never render as "Nee"; lid info belongs in `usage`, not in cons.
  **Why:** spec-mandated trust rule; showing unknown as "No" misinforms buyers.
  **How to apply:** any new vershoudbakjes product/variant data must use the usage schema; validator raises on bad schema.
- Copied/suspect records (BergHOFF, Glasslock, KitchenBrothers, OXO 6-delig) contain text copied from other brands; never add facts to them — the import validator warns, fixes need user-verified data.
- Editorial: max 3 pros / 2 cons; banned filler phrases like "Nederlands kwaliteitsmerk" and "Controleer of..."-advice.
- Litre labels always Dutch comma ("1,2 L"); no capacity values in `shape` fields.
