/** @type {import('jest').Config} */
module.exports = {
  preset: 'jest-expo',
  setupFiles: ['./jest.polyfills.js', './jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|react-native-svg|nativewind|react-native-css-interop|@gluestack-ui/.*|@react-aria/.*|@react-stately/.*|@react-types/.*|react-aria|react-stately|tailwind-variants))',
  ],
  // Each worker loads the whole RN + Gluestack graph (~1 GB). Using every core starves RAM on dev machines and CI,
  // and the first render of a file then exceeds the 5 s default. Fewer workers plus a roomier timeout fix that.
  maxWorkers: '50%',
  testTimeout: 15000,
  testPathIgnorePatterns: ['/node_modules/', '/.expo/'],
  collectCoverageFrom: ['src/**/*.{ts,tsx}', '!src/**/*.d.ts'],
};
