const fs = require("fs");
const path = require("path");

exports.default = async function (context) {
  const appOutDir = context.appOutDir;
  const resourcesDir =
    context.packager.platform.name === "mac"
      ? path.join(appOutDir, `${context.packager.appInfo.productFilename}.app`, "Contents", "Resources")
      : path.join(appOutDir, "resources");

  const standaloneNM = path.join(
    resourcesDir,
    "app-content",
    "frontend",
    ".next",
    "standalone",
    "node_modules"
  );

  const projectRoot = path.resolve(__dirname, "..", "..");
  const sourceNM = path.join(
    projectRoot,
    "frontend",
    ".next",
    "standalone",
    "node_modules"
  );

  if (!fs.existsSync(sourceNM)) {
    console.error("Source node_modules not found:", sourceNM);
    return;
  }

  console.log(`Copying standalone node_modules to ${standaloneNM}`);
  fs.cpSync(sourceNM, standaloneNM, { recursive: true });
  console.log("Done copying node_modules");
};
