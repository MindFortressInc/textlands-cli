#!/usr/bin/env node
/**
 * Post-install script that downloads the appropriate binary for the platform.
 */

const https = require('https');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const VERSION = require('../package.json').version;
const REPO = 'textlands/cli';

function getPlatformBinary() {
  const platform = process.platform;
  const arch = process.arch;

  if (platform === 'darwin') {
    return arch === 'arm64' ? 'textlands-macos-arm64' : 'textlands-macos-x64';
  } else if (platform === 'linux') {
    return 'textlands-linux-x64';
  } else if (platform === 'win32') {
    return 'textlands-windows-x64.exe';
  }

  throw new Error(`Unsupported platform: ${platform}-${arch}`);
}

function download(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);

    const request = (url) => {
      https.get(url, (response) => {
        // Handle redirects
        if (response.statusCode === 302 || response.statusCode === 301) {
          request(response.headers.location);
          return;
        }

        if (response.statusCode !== 200) {
          reject(new Error(`Failed to download: ${response.statusCode}`));
          return;
        }

        response.pipe(file);
        file.on('finish', () => {
          file.close();
          resolve();
        });
      }).on('error', (err) => {
        fs.unlink(dest, () => {});
        reject(err);
      });
    };

    request(url);
  });
}

async function main() {
  try {
    const binaryName = getPlatformBinary();
    const url = `https://github.com/${REPO}/releases/download/v${VERSION}/${binaryName}`;
    const binDir = path.join(__dirname, '..', 'bin');
    const dest = path.join(binDir, 'textlands' + (process.platform === 'win32' ? '.exe' : ''));

    // Create bin directory
    if (!fs.existsSync(binDir)) {
      fs.mkdirSync(binDir, { recursive: true });
    }

    console.log(`Downloading TextLands CLI v${VERSION}...`);
    console.log(`  Platform: ${process.platform}-${process.arch}`);
    console.log(`  Binary: ${binaryName}`);

    await download(url, dest);

    // Make executable on Unix
    if (process.platform !== 'win32') {
      fs.chmodSync(dest, 0o755);
    }

    console.log('TextLands CLI installed successfully!');
    console.log('Run `textlands --help` to get started.');

  } catch (error) {
    console.error('Failed to install TextLands CLI:', error.message);
    console.error('');
    console.error('You can also install via pip: pip install textlands');
    process.exit(1);
  }
}

main();
