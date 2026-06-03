import js from '@eslint/js'
import globals from 'globals'
import reactPlugin from 'eslint-plugin-react'
import reactHooksPlugin from 'eslint-plugin-react-hooks'
import tsParser from '@typescript-eslint/parser'
import tsPlugin from '@typescript-eslint/eslint-plugin'

const reactRules = {
  ...reactPlugin.configs.recommended.rules,
  ...reactHooksPlugin.configs.recommended.rules,
  'react/react-in-jsx-scope': 'off',
  'react/prop-types': 'off',
  'react/no-unescaped-entities': 'off',
  'react-hooks/exhaustive-deps': 'warn',
  'react-hooks/rules-of-hooks': 'error',
  'react-hooks/set-state-in-effect': 'warn',
}

export default [
  js.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    plugins: {
      react: reactPlugin,
      'react-hooks': reactHooksPlugin,
      '@typescript-eslint': tsPlugin,
    },
    languageOptions: {
      parser: tsParser,
      globals: { ...globals.browser },
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    settings: { react: { version: '19.0.0' } },
    rules: {
      ...reactRules,
      ...tsPlugin.configs.recommended.rules,
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-unused-vars': 'off',
    },
  },
  {
    files: ['src/**/__tests__/**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      globals: { ...globals.browser, ...globals.node },
    },
  },
]
