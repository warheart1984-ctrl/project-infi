import path from 'node:path';
import HtmlWebpackPlugin from 'html-webpack-plugin';

const config = {
  mode: 'development',
  entry: {
    main: path.resolve(process.cwd(), 'src/index.tsx'),
  },
  devtool: 'source-map',
  output: {
    path: path.resolve(process.cwd(), 'dist'),
    filename: 'assets/[name].js',
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
  plugins: [
    new HtmlWebpackPlugin({
      template: path.resolve(process.cwd(), 'public/index.html'),
      filename: 'index.html',
      scriptLoading: 'defer',
    }),
  ],
  devServer: {
    static: [
      {
        directory: path.resolve(process.cwd(), 'public'),
      },
      {
        directory: path.resolve(process.cwd(), 'dist'),
      },
    ],
    hot: true,
    historyApiFallback: true,
    compress: true,
    port: 5174,
    host: '127.0.0.1',
  },
};

export default config;
