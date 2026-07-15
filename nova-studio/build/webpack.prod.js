import path from 'node:path';
import HtmlWebpackPlugin from 'html-webpack-plugin';

const config = {
  mode: 'production',
  entry: {
    main: path.resolve(process.cwd(), 'src/index.tsx'),
  },
  output: {
    path: path.resolve(process.cwd(), 'dist'),
    filename: 'assets/[name].[contenthash].js',
    clean: true,
    publicPath: '/',
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js'],
    conditionNames: ['import', 'module', 'browser', 'default'],
    alias: {
      '@aaes-os/operator-config': path.resolve(process.cwd(), '..', 'packages', 'operator-config', 'src', 'index.ts'),
    },
  },
  module: {
    rules: [
      {
        test: /\.[jt]sx?$/,
        use: {
          loader: 'ts-loader',
          options: {
            configFile: path.resolve(process.cwd(), 'tsconfig.json'),
            transpileOnly: true,
          },
        },
        exclude: /node_modules/,
      },
    ],
  },
  optimization: {
    splitChunks: {
      chunks: 'all',
    },
    minimize: true,
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: path.resolve(process.cwd(), 'public/index.html'),
      filename: 'index.html',
      scriptLoading: 'defer',
    }),
  ],
};

export default config;
