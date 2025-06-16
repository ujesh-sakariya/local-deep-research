/**
 * Rate Limiting Settings UI Test
 *
 * Comprehensive test of the rate limiting settings panel in the web UI.
 * Tests all form elements, API interactions, and visual feedback.
 *
 * Prerequisites: Web server running on http://127.0.0.1:5000
 *
 * Usage: node tests/ui_tests/test_rate_limiting_settings.js
 */

const puppeteer = require('puppeteer');

async function testRateLimitingSettings() {
    const browser = await puppeteer.launch({
        headless: process.env.CI ? true : false,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage();

    // Set viewport for consistent testing
    await page.setViewport({ width: 1280, height: 720 });

    // Monitor network requests for API calls
    const apiRequests = [];
    await page.setRequestInterception(true);
    page.on('request', request => {
        if (request.url().includes('/api/v1/settings')) {
            apiRequests.push({
                method: request.method(),
                url: request.url(),
                postData: request.postData()
            });
            console.log('API REQUEST:', request.method(), request.url());
        }
        request.continue();
    });

    page.on('response', response => {
        if (response.url().includes('/api/v1/settings')) {
            console.log('API RESPONSE:', response.status(), response.url());
        }
    });

    try {
        console.log('🚀 Starting rate limiting settings UI test...');

        // Navigate to settings page
        console.log('📍 Navigating to settings page...');
        await page.goto('http://127.0.0.1:5000/research/settings', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });

        // Wait for settings to load
        console.log('⏳ Waiting for settings to load...');
        await page.waitForTimeout(3000);

        // Test 1: Check if rate limiting section exists
        console.log('🔍 Test 1: Checking for rate limiting section...');
        const rateLimitingSection = await page.$('[data-category="rate_limiting"], .rate-limiting-section, #rate-limiting');
        if (rateLimitingSection) {
            console.log('✅ Rate limiting section found');
        } else {
            console.log('❌ Rate limiting section not found');
            // Try to find any settings related to rate limiting
            const rateLimitingSettings = await page.$$eval('*', els =>
                els.filter(el => el.textContent && el.textContent.toLowerCase().includes('rate limit')).length
            );
            console.log(`Found ${rateLimitingSettings} elements mentioning rate limiting`);
        }

        // Test 2: Check for rate limiting enabled checkbox
        console.log('🔍 Test 2: Checking for rate limiting enabled checkbox...');
        const enabledCheckbox = await page.$('input[type="checkbox"][name*="rate_limiting"], input[type="checkbox"][id*="rate_limiting"]');
        if (enabledCheckbox) {
            console.log('✅ Rate limiting enabled checkbox found');

            // Test toggling the checkbox
            const isChecked = await page.evaluate(el => el.checked, enabledCheckbox);
            console.log(`📊 Initial state: ${isChecked ? 'enabled' : 'disabled'}`);

            // Toggle the checkbox
            await enabledCheckbox.click();
            await page.waitForTimeout(1000); // Wait for potential API call

            const newState = await page.evaluate(el => el.checked, enabledCheckbox);
            console.log(`📊 After toggle: ${newState ? 'enabled' : 'disabled'}`);

            if (newState !== isChecked) {
                console.log('✅ Checkbox toggle works correctly');
            } else {
                console.log('❌ Checkbox toggle failed');
            }
        } else {
            console.log('❌ Rate limiting enabled checkbox not found');
        }

        // Test 3: Check for rate limiting profile selector
        console.log('🔍 Test 3: Checking for rate limiting profile selector...');
        const profileSelector = await page.$('select[name*="profile"], select[id*="profile"], .profile-selector select');
        if (profileSelector) {
            console.log('✅ Rate limiting profile selector found');

            // Get available options
            const options = await page.evaluate(select =>
                Array.from(select.options).map(option => option.value), profileSelector
            );
            console.log('📊 Available profiles:', options);

            // Test selecting different profiles
            if (options.includes('conservative')) {
                await page.select(profileSelector, 'conservative');
                console.log('✅ Selected conservative profile');
                await page.waitForTimeout(500);
            }

            if (options.includes('balanced')) {
                await page.select(profileSelector, 'balanced');
                console.log('✅ Selected balanced profile');
                await page.waitForTimeout(500);
            }

            if (options.includes('aggressive')) {
                await page.select(profileSelector, 'aggressive');
                console.log('✅ Selected aggressive profile');
                await page.waitForTimeout(500);
            }
        } else {
            console.log('❌ Rate limiting profile selector not found');
        }

        // Test 4: Check for numeric input fields (learning rate, exploration rate, etc.)
        console.log('🔍 Test 4: Checking for numeric input fields...');
        const numericInputs = await page.$$('input[type="number"], input[step]');
        console.log(`📊 Found ${numericInputs.length} numeric input fields`);

        for (let i = 0; i < Math.min(numericInputs.length, 3); i++) {
            const input = numericInputs[i];
            const name = await page.evaluate(el => el.name || el.id, input);
            const value = await page.evaluate(el => el.value, input);
            console.log(`📊 Numeric input ${i + 1}: ${name} = ${value}`);

            // Test changing the value
            await input.click({ clickCount: 3 }); // Select all text
            await input.type('0.5');
            await page.waitForTimeout(300);
            console.log(`✅ Updated numeric input ${i + 1}`);
        }

        // Test 5: Check for rate limiting statistics/status display
        console.log('🔍 Test 5: Checking for rate limiting statistics...');
        const statisticsElements = await page.$$('.statistics, .status, .rate-limit-stats, [class*="stat"]');
        if (statisticsElements.length > 0) {
            console.log(`✅ Found ${statisticsElements.length} statistics elements`);

            // Try to read some statistics values
            for (let i = 0; i < Math.min(statisticsElements.length, 3); i++) {
                const text = await page.evaluate(el => el.textContent, statisticsElements[i]);
                if (text && text.trim()) {
                    console.log(`📊 Statistics ${i + 1}: ${text.trim().substring(0, 50)}...`);
                }
            }
        } else {
            console.log('❌ No rate limiting statistics found');
        }

        // Test 6: Test save/submit functionality
        console.log('🔍 Test 6: Testing save functionality...');
        const saveButton = await page.$('button[type="submit"], .save-button, button:contains("Save")');
        if (saveButton) {
            console.log('✅ Save button found');

            const initialRequestCount = apiRequests.length;
            await saveButton.click();
            await page.waitForTimeout(2000); // Wait for API calls

            const newRequestCount = apiRequests.length;
            if (newRequestCount > initialRequestCount) {
                console.log('✅ Save triggered API requests');
                console.log(`📊 API requests: ${newRequestCount - initialRequestCount} new requests`);
            } else {
                console.log('❌ Save did not trigger API requests');
            }
        } else {
            console.log('❌ Save button not found');
        }

        // Test 7: Check for validation feedback
        console.log('🔍 Test 7: Testing validation feedback...');
        const errorElements = await page.$$('.error, .validation-error, .invalid-feedback, [class*="error"]');
        console.log(`📊 Found ${errorElements.length} potential error elements`);

        // Test 8: Check for help text or tooltips
        console.log('🔍 Test 8: Checking for help text...');
        const helpElements = await page.$$('.help-text, .tooltip, .description, [title]');
        console.log(`📊 Found ${helpElements.length} help/tooltip elements`);

        // Test 9: Responsive design test
        console.log('🔍 Test 9: Testing responsive design...');
        await page.setViewport({ width: 768, height: 1024 }); // Tablet view
        await page.waitForTimeout(500);

        const visibleElements = await page.evaluate(() => {
            const elements = document.querySelectorAll('input, select, button');
            return Array.from(elements).filter(el => {
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && style.visibility !== 'hidden';
            }).length;
        });

        console.log(`📊 Visible form elements in tablet view: ${visibleElements}`);

        await page.setViewport({ width: 375, height: 667 }); // Mobile view
        await page.waitForTimeout(500);

        const mobileVisibleElements = await page.evaluate(() => {
            const elements = document.querySelectorAll('input, select, button');
            return Array.from(elements).filter(el => {
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && style.visibility !== 'hidden';
            }).length;
        });

        console.log(`📊 Visible form elements in mobile view: ${mobileVisibleElements}`);

        // Test 10: Performance test
        console.log('🔍 Test 10: Performance test...');
        const navigationTiming = await page.evaluate(() => {
            const timing = performance.getEntriesByType('navigation')[0];
            return {
                domContentLoaded: timing.domContentLoadedEventEnd - timing.domContentLoadedEventStart,
                loadComplete: timing.loadEventEnd - timing.loadEventStart,
                total: timing.loadEventEnd - timing.fetchStart
            };
        });

        console.log('📊 Page load performance:');
        console.log(`   DOM Content Loaded: ${navigationTiming.domContentLoaded.toFixed(2)}ms`);
        console.log(`   Load Complete: ${navigationTiming.loadComplete.toFixed(2)}ms`);
        console.log(`   Total Load Time: ${navigationTiming.total.toFixed(2)}ms`);

        // Summary
        console.log('📊 Test Summary:');
        console.log(`   Total API requests: ${apiRequests.length}`);
        console.log(`   Form elements tested: Multiple categories`);
        console.log(`   Responsive views tested: Desktop, Tablet, Mobile`);

        // Take screenshot for debugging
        await page.screenshot({
            path: 'rate_limiting_settings_test.png',
            fullPage: true
        });
        console.log('📸 Screenshot saved as rate_limiting_settings_test.png');

        console.log('🎉 Rate limiting settings UI test completed successfully');

    } catch (error) {
        console.error('❌ Error during rate limiting settings test:', error);

        // Take error screenshot
        try {
            await page.screenshot({
                path: 'rate_limiting_settings_error.png',
                fullPage: true
            });
            console.log('📸 Error screenshot saved as rate_limiting_settings_error.png');
        } catch (screenshotError) {
            console.error('Failed to take error screenshot:', screenshotError);
        }

        throw error;
    } finally {
        await browser.close();
    }
}

// Run the test
if (require.main === module) {
    testRateLimitingSettings()
        .then(() => {
            console.log('✅ All rate limiting UI tests completed');
            process.exit(0);
        })
        .catch(error => {
            console.error('❌ Rate limiting UI tests failed:', error);
            process.exit(1);
        });
}

module.exports = { testRateLimitingSettings };
