const js = require('@eslint/js');

module.exports = [
    js.configs.recommended,
    {
        ignores: ['node_modules/**', 'build/**', 'public/**'],
    },
    {
        files: ['**/*.js', '**/*.jsx'],
        languageOptions: {
            ecmaVersion: 2022,
            sourceType: 'module',
            globals: {
                console: 'readonly',
                process: 'readonly',
                window: 'readonly',
                document: 'readonly',
                navigator: 'readonly',
                localStorage: 'readonly',
            },
        },
        rules: {
            'no-unused-vars': 'warn',
            'no-undef': 'error',
        },
    },
];