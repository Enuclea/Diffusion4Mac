const { notarize } = require('electron-notarize');
const path = require('path');

module.exports = async function (context) {
  const { electronPlatformName, appOutDir } = context;  
  if (electronPlatformName !== 'darwin') {
    return;
  }

  const appName = context.packager.appInfo.productFilename;
  const appPath = path.join(appOutDir, `${appName}.app`);

  // Only notarize if credentials are provided in the environment
  const appleId = process.env.APPLE_ID;
  const appleIdPassword = process.env.APPLE_ID_PASSWORD;
  const teamId = process.env.APPLE_TEAM_ID;

  if (!appleId || !appleIdPassword || !teamId) {
    console.warn('Skipping Apple notarization: APPLE_ID, APPLE_ID_PASSWORD, or APPLE_TEAM_ID env vars are missing.');
    return;
  }

  console.log(`Starting Apple notarization for ${appName}...`);

  try {
    await notarize({
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
