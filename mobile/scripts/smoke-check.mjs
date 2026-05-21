import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const mobileRoot = process.cwd();
const repoRoot = path.resolve(mobileRoot, '..');

const checks = [];

function readJson(relativePath) {
  const filePath = path.join(mobileRoot, relativePath);
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function readTextFromRepo(relativePath) {
  return fs.readFileSync(path.join(repoRoot, relativePath), 'utf8');
}

function existsFromMobile(relativePath) {
  return fs.existsSync(path.join(mobileRoot, relativePath));
}

function check(name, predicate) {
  checks.push({ name, ok: Boolean(predicate()) });
}

const appConfig = readJson('app.json').expo;
const easConfig = readJson('eas.json');
const packageJson = readJson('package.json');
const apiClient = readTextFromRepo('mobile/src/api/client.ts');
const mobileReadme = readTextFromRepo('mobile/README.md');
const rootReadme = readTextFromRepo('README.md');
const setupDoc = readTextFromRepo('docs/setup/local_setup.md');

check('Expo project id is configured', () => Boolean(appConfig.extra?.eas?.projectId));
check('EAS update URL uses the project id', () => appConfig.updates?.url?.includes(appConfig.extra.eas.projectId));
check('Runtime version follows app version', () => appConfig.runtimeVersion?.policy === 'appVersion');
check('Preview build channel is configured', () => easConfig.build?.preview?.channel === 'preview');
check('Tablet support is enabled for iOS', () => appConfig.ios?.supportsTablet === true);
check('Mobile app has no OpenAI key dependency', () => !JSON.stringify(packageJson).includes('OPENAI_API_KEY'));
check('Mobile API client sends backend access token header', () => apiClient.includes('X-StudyPilot-Key'));
check('Mobile API client keeps a local default backend URL', () => apiClient.includes('http://127.0.0.1:8000'));
check('EAS preview update script exists', () => packageJson.scripts?.['update:preview']?.includes('eas-cli'));
check('expo-updates dependency exists', () => Boolean(packageJson.dependencies?.['expo-updates']));
check('Mobile README documents preview updates', () => mobileReadme.includes('Preview Updates Without A Local Dev Server'));
check('Root README links to setup guide', () => rootReadme.includes('docs/setup/local_setup.md'));
check('Setup guide documents preview update command', () => setupDoc.includes('npm run update:preview'));

[
  'app/index.tsx',
  'app/settings.tsx',
  'app/courses/index.tsx',
  'app/courses/new.tsx',
  'app/courses/[courseId].tsx',
  'app/sections/[sectionId].tsx',
  'app/documents/index.tsx',
  'app/documents/[documentId].tsx',
  'app/documents/[documentId]/text.tsx',
  'app/summaries/[summaryId].tsx',
  'app/quiz/[quizId].tsx',
  'app/schedule/course/[courseId].tsx',
  'app/study/course/[courseId].tsx',
].forEach((route) => {
  check(`Route exists: ${route}`, () => existsFromMobile(route));
});

const failed = checks.filter((item) => !item.ok);
for (const item of checks) {
  console.log(`${item.ok ? 'PASS' : 'FAIL'} ${item.name}`);
}

if (failed.length) {
  console.error(`\n${failed.length} mobile smoke check(s) failed.`);
  process.exit(1);
}

console.log(`\n${checks.length} mobile smoke checks passed.`);
