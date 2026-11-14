import {defineConfig} from '@playwright/test';
export default defineConfig({outputDir:'test-results-production',testDir:'./tests',testMatch:'**/production.spec.ts',use:{baseURL:'http://127.0.0.1:4185',headless:true,channel:'msedge'},webServer:{command:'npm run preview -- --port 4185',url:'http://127.0.0.1:4185',reuseExistingServer:false,timeout:30000}});

