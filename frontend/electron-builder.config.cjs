const fs = require('node:fs')
const path = require('node:path')

const hasSigningIdentity = Boolean(process.env.MAC_CODE_SIGN_IDENTITY)
const shouldNotarize = hasSigningIdentity && Boolean(
  process.env.APPLE_ID &&
    process.env.APPLE_APP_SPECIFIC_PASSWORD &&
    process.env.APPLE_TEAM_ID
)
const macBackendSidecar = path.join(__dirname, 'resources', 'backend', 'cybopal-api')

function verifyMacBackendSidecar(context) {
  if (context.electronPlatformName !== 'darwin') {
    return
  }

  if (!fs.existsSync(macBackendSidecar)) {
    throw new Error(
      [
        'Missing macOS backend sidecar: resources/backend/cybopal-api.',
        'Run `bash scripts/build-macos-app.sh` from the repository root on macOS.',
        'The packaged app must include the FastAPI sidecar so operators can launch it by double-clicking.'
      ].join(' ')
    )
  }

  fs.chmodSync(macBackendSidecar, 0o755)
}

module.exports = {
  appId: 'com.cybopal.factorytool',
  productName: 'CyboPal Factory Tool',
  electronVersion: '33.4.11',
  copyright: 'Copyright (c) CyboPal',
  asar: true,
  directories: {
    output: 'release'
  },
  files: ['dist/**/*', 'electron/**/*'],
  extraResources: [
    {
      from: 'resources/backend/cybopal-api',
      to: 'backend/cybopal-api'
    }
  ],
  beforePack: verifyMacBackendSidecar,
  mac: {
    category: 'public.app-category.utilities',
    target: ['dmg'],
    hardenedRuntime: hasSigningIdentity,
    gatekeeperAssess: false,
    identity: hasSigningIdentity ? process.env.MAC_CODE_SIGN_IDENTITY : null,
    binaries: ['Contents/Resources/backend/cybopal-api'],
    artifactName: '${productName}-${version}-${arch}.${ext}'
  },
  dmg: {
    artifactName: '${productName}-${version}-${arch}.${ext}',
    contents: [
      { x: 130, y: 220 },
      { x: 410, y: 220, type: 'link', path: '/Applications' }
    ]
  },
  afterSign: shouldNotarize ? path.join(__dirname, 'scripts/notarize.cjs') : undefined
}
