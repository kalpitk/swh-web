/**
 * Copyright (C) 2018  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// webpack configuration for compiling static assets in production mode

// import required webpack plugins
const UglifyJsPlugin = require('uglifyjs-webpack-plugin');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');

// import webpack development configuration
var webpackProdConfig = require('./webpack.config.development');

// override mode to production
webpackProdConfig.mode = 'production';

// configure minimizer for js and css assets
webpackProdConfig.optimization.minimizer = [
  // use ugligyjs for minimizing js and generate source map files
  new UglifyJsPlugin({
    cache: true,
    parallel: true,
    sourceMap: true
  }),
  // use cssnano for minimizing css and generate source map files
  new OptimizeCSSAssetsPlugin({
    cssProcessorOptions: {
      map: {
        inline: false
      },
      minifyFontValues: false,
      discardUnused: false,
      zindex: false
    }
  })
];

// webpack production configuration
module.exports = webpackProdConfig;
