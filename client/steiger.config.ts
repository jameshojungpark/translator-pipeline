import fsd from "@feature-sliced/steiger-plugin";
import { defineConfig } from "steiger";

export default defineConfig([
  ...fsd.configs.recommended,
  {
    rules: {
      // With only the viewer page migrated, every slice necessarily has a
      // single referencing page. Re-enable once the host page is migrated
      // and slices are shared between pages.
      "fsd/insignificant-slice": "off",
    },
  },
]);
