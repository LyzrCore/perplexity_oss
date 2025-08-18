import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import typescript from '@rollup/plugin-typescript';
import babel from '@rollup/plugin-babel';
import pkg from './package.json';

export default [
  {
    input: 'src/index.ts',
    output: [
      {
        file: pkg.main,
        format: 'iife',
        name: 'lyzr',
        sourcemap: true,
        extend: true,
        globals: {}
      },
      {
        file: 'dist/index.esm.js',
        format: 'esm',
        sourcemap: true
      }
    ],
    plugins: [
      typescript(),
      resolve({
        browser: true,
        preferBuiltins: false
      }),
      commonjs({
        transformMixedEsModules: true,
        include: /node_modules/
      }),
      babel({
        babelHelpers: 'bundled',
        exclude: 'node_modules/**'
      })
    ]
  }
];
