import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    rules: {
      // 일시적으로 완화된 규칙들 (단계적 개선 예정)
      "@typescript-eslint/no-explicit-any": "warn", // Error → Warning
      "@typescript-eslint/no-unused-vars": "warn",  // Error → Warning  
      "@typescript-eslint/no-require-imports": "warn", // Error → Warning
    }
  }
];

export default eslintConfig;
