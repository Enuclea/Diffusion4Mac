const { notarize } = require('electron-notarize');
const path = require('path');

module.exports = async function (context) {
  const { electronPlatformName, appOutDir } = context;  
  if (electronPlatformName !== 'darwin') {
    return;
  }

  const appName = context.packager.appInfo.productFilename;
  const appPath = path.join(appOutDir, `${appName}.app`);

  // Only notarize if credentials are provided in the environment or .env
  let appleId = process.env.APPLE_ID;
  let appleIdPassword = process.env.APPLE_ID_PASSWORD;
  let teamId = process.env.APPLE_TEAM_ID;

  if (!appleId || !appleIdPassword || !teamId) {
    const fs = require('fs');
    const envPath = path.join(__dirname, '..', '.env');
    if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, 'utf8');
      envContent.split('\n').forEach(line => {
        if (line.includes('=') && !line.trim().startsWith('#')) {
          const parts = line.split('=');
          const key = parts[0].trim();
          const val = parts.slice(1).join('=').trim();
          if (key === 'APPLE_ID') appleId = val;
          if (key === 'APPLE_ID_PASSWORD') appleIdPassword = val;
          if (key === 'APPLE_TEAM_ID') teamId = val;
        }
      });
    }
  }

  if (!appleId || !appleIdPassword || !teamId) {
    console.warn('Skipping Apple notarization: APPLE_ID, APPLE_ID_PASSWORD, or APPLE_TEAM_ID env vars/keys in .env are missing.');
    return;
  }

  console.log(`Starting Apple notarization for ${appName}...`);

  try {
    await notarize({
      tool: 'notarytool',
      appBundleId: 'com.diffusion4mac.diffusion4mac',
      appPath: appPath,
      appleId: appleId,
      appleIdPassword: appleIdPassword,
      teamId: teamId,
    });
    console.log('Apple notarization completed successfully!');
  } catch (error) {
    console.error('Apple notarization failed:', error);
    throw error;
  }
};
