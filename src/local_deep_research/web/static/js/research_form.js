/**
 * Research form handling with settings management and warnings
 */

// Global settings cache for warning logic
let globalSettings = {};

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the research form
    console.log('DOM loaded, initializing research form');
    initResearchForm();
});

/**
 * Initialize the research form with values from settings
 */
function initResearchForm() {
    console.log('Initializing research form...');
    // Get form elements
    const iterationsInput = document.getElementById('iterations');
    const questionsInput = document.getElementById('questions_per_iteration');

    // Fetch all settings at once (more efficient)
    fetch('/research/settings/api')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch settings');
            }
            return response.json();
        })
        .then(data => {
            console.log('Loaded settings:', data);
            if (data && data.status === 'success' && data.settings) {
                // Find our specific settings
                const settings = data.settings;

                // Cache settings globally for warning logic
                globalSettings = settings;

                // Look for the iterations setting
                for (const key in settings) {
                    const setting = settings[key];
                    if (key === 'search.iterations') {
                        console.log('Found iterations setting:', setting.value);
                        iterationsInput.value = setting.value;
                    }

                    if (key === 'search.questions_per_iteration') {
                        console.log('Found questions setting:', setting.value);
                        questionsInput.value = setting.value;
                    }
                }

                // Initialize warnings after settings are loaded
                initializeWarnings();
            }
        })
        .catch(error => {
            console.warn('Error loading research settings:', error);
            // Form will use default values if settings can't be loaded
        });

    // Add our settings saving to the form submission process
    patchFormSubmitHandler();
}

/**
 * Patch the existing form submit handler to include our settings saving functionality
 */
function patchFormSubmitHandler() {
    // Get the form element
    const form = document.getElementById('research-form');
    if (!form) return;

    // Monitor for form submissions using the capture phase to run before other handlers
    form.addEventListener('submit', function(event) {
        // Save research settings first, before the main form handler processes the submission
        saveResearchSettings();

        // Let the event continue normally to the other handlers
    }, true); // true enables capture phase
}

/**
 * Save research settings to the database
 */
function saveResearchSettings() {
    const iterations = document.getElementById('iterations').value;
    const questions = document.getElementById('questions_per_iteration').value;

    console.log('Saving research settings:', { iterations, questions });

    // Get CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // Save settings
    fetch('/research/settings/save_all_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            'search.iterations': parseInt(iterations),
            'search.questions_per_iteration': parseInt(questions)
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Settings saved:', data);
    })
    .catch(error => {
        console.warn('Error saving research settings:', error);
    });
}

/**
 * Initialize warning system
 */
function initializeWarnings() {
    console.log('Initializing warning system...');

    // Check warnings on form load
    checkAndDisplayWarnings();

    // Monitor form changes for dynamic warnings
    setupWarningListeners();
}

/**
 * Setup event listeners for settings changes
 */
function setupWarningListeners() {
    // Monitor provider changes directly and refetch settings
    const providerSelect = document.getElementById('model_provider');
    if (providerSelect) {
        providerSelect.addEventListener('change', function() {
            console.log('Provider changed to:', providerSelect.value);
            // Wait a bit longer for the saveProviderSetting API call to complete
            setTimeout(refetchSettingsAndUpdateWarnings, 500);
        });
    }

    // Hook into the existing saveProviderSetting function if it exists
    // This will trigger when the research.js calls saveProviderSetting
    if (typeof window.saveProviderSetting === 'function') {
        const originalSaveProviderSetting = window.saveProviderSetting;
        window.saveProviderSetting = function(providerValue) {
            console.log('Intercepted saveProviderSetting call:', providerValue);
            // Call the original function
            const result = originalSaveProviderSetting.apply(this, arguments);
            // After it completes, refetch settings and update warnings
            setTimeout(refetchSettingsAndUpdateWarnings, 200);
            return result;
        };
    }

    const strategySelect = document.getElementById('strategy');
    if (strategySelect) {
        strategySelect.addEventListener('change', function() {
            console.log('Strategy changed to:', strategySelect.value);
            setTimeout(checkAndDisplayWarnings, 100);
        });
    }

    // Use Socket.IO to listen for settings changes if available (backup)
    if (typeof io !== 'undefined') {
        const socket = io();
        socket.on('settings_changed', function(data) {
            console.log('Settings changed via WebSocket:', data);
            // Update global settings cache
            if (data.settings) {
                Object.assign(globalSettings, data.settings);
            }
            // Recheck warnings with new settings
            setTimeout(checkAndDisplayWarnings, 100);
        });

        socket.on('connect', function() {
            console.log('Connected to settings WebSocket');
        });
    }
}

/**
 * Refetch settings from the server and update warnings
 */
function refetchSettingsAndUpdateWarnings() {
    console.log('Refetching settings from server...');

    fetch('/research/settings/api')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch settings');
            }
            return response.json();
        })
        .then(data => {
            console.log('Refetched settings:', data);
            if (data && data.status === 'success' && data.settings) {
                // Update global settings cache
                globalSettings = data.settings;
                // Recheck warnings with fresh settings
                setTimeout(checkAndDisplayWarnings, 100);
            }
        })
        .catch(error => {
            console.warn('Error refetching settings:', error);
            // Fallback to checking warnings with current settings
            setTimeout(checkAndDisplayWarnings, 100);
        });
}

// Make functions globally available for other scripts
window.refetchSettingsAndUpdateWarnings = refetchSettingsAndUpdateWarnings;
window.displayWarnings = displayWarnings;

/**
 * Check warning conditions and display warnings
 */
function checkAndDisplayWarnings() {
    console.log('Checking warning conditions...');

    // Get provider from database settings (source of truth)
    const provider = getSetting('llm.provider', 'ollama').toLowerCase();
    const strategy = getCurrentStrategy();
    const model = getCurrentModel();

    // Debug logging
    console.log('Current values:', { provider, strategy, model });

    // Get context settings
    const localContext = getSetting('llm.local_context_window_size', 4096);
    const cloudUnrestricted = getSetting('llm.context_window_unrestricted', true);
    const cloudContext = getSetting('llm.context_window_size', 128000);

    console.log('Context settings:', { localContext, cloudUnrestricted, cloudContext });

    // Get dismissal settings
    const dismissHighContext = getSetting('app.warnings.dismiss_high_context', false);
    const dismissLowContextFocused = getSetting('app.warnings.dismiss_low_context_focused', false);
    const dismissModelMismatch = getSetting('app.warnings.dismiss_model_mismatch', false);

    const warnings = [];

    // Check warning conditions
    const isLocalProvider = provider === 'ollama' || provider === 'llamacpp' || provider === 'lmstudio' || provider === 'vllm';

    console.log('Provider analysis:', {
        rawProvider: provider,
        isLocal: isLocalProvider,
        cloudUnrestricted,
        allSettings: Object.keys(globalSettings).filter(k => k.includes('context') || k.includes('warning'))
    });

    // Get effective context size based on provider type
    let effectiveContext;
    if (isLocalProvider) {
        effectiveContext = localContext;
    } else {
        // Cloud provider: check if unrestricted or has limit
        if (cloudUnrestricted) {
            effectiveContext = 200000; // Assume high context for unrestricted cloud
        } else {
            effectiveContext = cloudContext;
        }
    }

    console.log('Effective context for warnings:', effectiveContext, 'Provider type:', isLocalProvider ? 'local' : 'cloud');

    if (isLocalProvider && localContext > 8192 && !dismissHighContext) {
        warnings.push({
            type: 'high_context',
            icon: '⚠️',
            title: 'High Context Warning',
            message: `Context size (${localContext.toLocaleString()} tokens) may cause memory issues with ${provider}. Increase VRAM or reduce context size if you experience slowdowns.`,
            dismissKey: 'app.warnings.dismiss_high_context'
        });
    }

    if (strategy === 'focused-iteration' && effectiveContext < 32000 && !dismissLowContextFocused) {
        const providerType = isLocalProvider ? 'local' : 'cloud';
        const contextSource = isLocalProvider ? 'local context setting' : (cloudUnrestricted ? 'unrestricted cloud context' : 'cloud context setting');

        warnings.push({
            type: 'low_context_focused',
            icon: '💡',
            title: 'Strategy Recommendation',
            message: `Focused iteration works best with 32k+ context tokens. Current ${providerType} provider has ${effectiveContext.toLocaleString()} tokens (${contextSource}). Consider increasing context size or using source-based strategy.`,
            dismissKey: 'app.warnings.dismiss_low_context_focused'
        });
    }

    if (model && model.includes('70b') && isLocalProvider && localContext > 8192 && !dismissModelMismatch) {
        warnings.push({
            type: 'model_mismatch',
            icon: '🧠',
            title: 'Model & Context Warning',
            message: `Large model (${model}) with high context (${localContext.toLocaleString()}) may exceed VRAM. Consider reducing context size or upgrading GPU memory.`,
            dismissKey: 'app.warnings.dismiss_model_mismatch'
        });
    }

    // SearXNG recommendation: more questions instead of more iterations
    const searchEngine = getSetting('search.tool', 'duckduckgo').toLowerCase();
    const iterations = parseInt(getSetting('search.iterations', 2));
    const questionsPerIteration = parseInt(getSetting('search.questions_per_iteration', 3));
    const dismissSearxngRecommendation = getSetting('app.warnings.dismiss_searxng_recommendation', false);

    console.log('SearXNG check:', { searchEngine, iterations, questionsPerIteration, dismissSearxngRecommendation });

    if (searchEngine === 'searxng' && iterations > 2 && !dismissSearxngRecommendation) {
        warnings.push({
            type: 'searxng_recommendation',
            icon: '💡',
            title: 'SearXNG Optimization Tip',
            message: `For SearXNG, we recommend using more questions per iteration (${questionsPerIteration} → 10) instead of more iterations (${iterations}). SearXNG handles multiple questions efficiently in a single iteration.`,
            dismissKey: 'app.warnings.dismiss_searxng_recommendation'
        });
    }

    // Display warnings
    displayWarnings(warnings);
}

/**
 * Display warnings in the alert container
 */
function displayWarnings(warnings) {
    const alertContainer = document.getElementById('research-alert');
    if (!alertContainer) return;

    if (warnings.length === 0) {
        alertContainer.style.display = 'none';
        alertContainer.innerHTML = '';
        return;
    }

    const warningsHtml = warnings.map(warning => {
        // Use green styling for recommendations/tips
        const isRecommendation = warning.type === 'searxng_recommendation';
        const bgColor = isRecommendation ? '#d4edda' : '#fff3cd';
        const borderColor = isRecommendation ? '#c3e6cb' : '#ffeaa7';
        const textColor = isRecommendation ? '#155724' : '#856404';

        return `
        <div class="warning-banner warning-${warning.type}" style="
            background: ${bgColor};
            border: 1px solid ${borderColor};
            border-radius: 6px;
            padding: 12px 16px;
            margin-bottom: 8px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
        ">
            <span style="font-size: 16px; flex-shrink: 0;">${warning.icon}</span>
            <div style="flex: 1;">
                <div style="font-weight: 600; color: ${textColor}; margin-bottom: 4px;">
                    ${warning.title}
                </div>
                <div style="color: ${textColor}; font-size: 14px; line-height: 1.4;">
                    ${warning.message}
                </div>
            </div>
            <button onclick="dismissWarning('${warning.dismissKey}')" style="
                background: none;
                border: none;
                color: ${textColor};
                cursor: pointer;
                padding: 4px;
                font-size: 16px;
                flex-shrink: 0;
            ">&times;</button>
        </div>
        `;
    }).join('');

    alertContainer.innerHTML = warningsHtml;
    alertContainer.style.display = 'block';
}

/**
 * Dismiss a warning by updating the setting
 */
function dismissWarning(dismissKey) {
    console.log('Dismissing warning:', dismissKey);

    // Get CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // Update dismissal setting
    fetch('/research/settings/save_all_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            [dismissKey]: true
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Warning dismissed:', data);
        // Update global settings cache
        globalSettings[dismissKey] = { value: true };
        // Recheck warnings
        checkAndDisplayWarnings();
    })
    .catch(error => {
        console.warn('Error dismissing warning:', error);
    });
}

/**
 * Helper functions to get current form values
 */
function getCurrentProvider() {
    const providerSelect = document.getElementById('model_provider');
    if (providerSelect && providerSelect.value) {
        return providerSelect.value.toLowerCase();
    }
    return 'ollama';
}

function getCurrentStrategy() {
    const strategySelect = document.getElementById('strategy');
    return strategySelect ? strategySelect.value : 'source-based';
}

function getCurrentModel() {
    // Try to get from model dropdown display
    const modelDisplay = document.querySelector('.model-dropdown .dropdown-display');
    return modelDisplay ? modelDisplay.textContent.trim() : '';
}

function getSetting(key, defaultValue) {
    return globalSettings[key] ? globalSettings[key].value : defaultValue;
}
