// Universal Scales - Main JavaScript Application
// Constants are imported from constants.js

class UniversalScales {
    constructor() {
        this.currentDimension = 'length';
        this.currentUnit = null;
        this.dimensionData = null;
        this.dimensionCatalog = [];
        this.dimensionCatalogBySlug = new Map();
        this.exchangeRates = null;
        this.notationMode = 'scientific'; // 'scientific', 'mathematical', 'human'

        // Initialize formatter
        this.formatter = new NumberFormatter(this.notationMode);

        // D3.js setup - will be initialized by plot renderer
        this.margin = CONFIG.MARGIN;
        this.width = 0;
        this.height = 0;
        this.svg = null;
        this.xScale = null;
        this.yScale = null;
        this.originalXDomain = null; // Store original domain for zoom reset
        this.zoomBehavior = null;
        this.isUpdatingTransform = false; // Flag to prevent recursive zoom updates
        this.dragStartY = null; // Track vertical drag start position for scrolling
        this.dragStartX = null; // Track horizontal drag start position
        this.isVerticalDrag = false; // Track if current drag is primarily vertical
        this.lastScrollDeltaY = null; // Track last scroll delta to prevent double-scrolling
        this.dragStartTransform = null; // Store transform at drag start to restore if vertical
        this.touchStartOnItem = null; // Track if touch started on item/label for mobile drag detection
        this.touchStartPosition = null; // Track initial touch position for drag detection
        this.enableAudioHandler = null; // Store reference to enableAudio handler for cleanup
        this.zoomUpdatePending = false; // Throttle zoom updates for performance
        this.actualItemExtent = null; // Store actual item extent (for zoom limits)
        this.originalItemsHeight = null; // Store original itemsHeight to preserve vertical layout when zoomed
        this.mainGroup = null; // Will be set by plot renderer
        this.zoomBackground = null; // Will be set by setupZoom
        this.tooltipPinned = false; // Track if tooltip is pinned (clicked on desktop)
        this.isResettingView = false; // Track when a programmatic reset is in progress
        this.buttonIntervals = {}; // Track active intervals for hold-down buttons

        // DOM elements
        this.dimensionSelect = document.getElementById('dimension-select');
        this.dimensionBrowserPanel = document.getElementById('dimension-browser-panel');
        this.dimensionBrowser = document.getElementById('dimension-browser');
        this.dimensionBrowserToggle = document.getElementById('dimension-browser-toggle');
        this.dimensionBrowserCurrent = document.getElementById('dimension-browser-current');
        this.dimensionBrowserSearch = document.getElementById('dimension-browser-search');
        this.dimensionBrowserEmpty = document.getElementById('dimension-browser-empty');
        this.unitSelect = document.getElementById('unit-select');
        this.unitBrowserPanel = document.getElementById('unit-browser-panel');
        this.unitBrowserList = document.getElementById('unit-browser-list');
        this.unitBrowserToggle = document.getElementById('unit-browser-toggle');
        this.unitBrowserCurrent = document.getElementById('unit-browser-current');
        this.notationToggle = document.getElementById('notation-toggle');
        this.darkModeToggle = document.getElementById('dark-mode-toggle');
        this.musicToggle = document.getElementById('music-toggle');
        this.backgroundMusic = document.getElementById('background-music');
        this.tooltip = document.getElementById('tooltip');
        this.tooltip?.addEventListener('pointerenter', () => this.cancelTooltipHide());
        this.tooltip?.addEventListener('pointerleave', () => {
            if (!this.tooltipPinned) this.scheduleTooltipHide();
        });
        this.plotContainer = document.getElementById('plot-container');
        this.imageModal = document.getElementById('image-modal');
        this.imageModalImg = document.getElementById('image-modal-img');
        this.imageModalClose = this.imageModal?.querySelector('.image-modal-close');
        this.topAxisBackground = null; // Will be created for fixed positioning
        this.dimensionDescription = document.getElementById('dimension-description');
        this.unitDescription = document.getElementById('unit-description');

        // Resources Panel elements
        this.resourcesPanel = document.getElementById('resources-panel');
        this.resourcesToggle = document.getElementById('resources-toggle');
        this.resourcesContent = document.getElementById('resources-content');

        // Custom items storage (merged with original data)
        this.customItems = {}; // key: dimension name, value: array of custom items

        // Cache for image existence checks to avoid repeated failed requests
        this.imageExistenceCache = new Map();
        this.isDimensionBrowserOpen = false;
        this.isUnitBrowserOpen = false;

        this.init();
    }

    async init() {
        // Set up event listeners
        this.setupEventListeners();

        // Initialize dark mode
        this.initDarkMode();

        // Initialize music
        this.initMusic();

        // Initialize notation
        this.initNotation();

        // Initialize editor
        this.editor = new ItemEditor(this);

        // Initialize plot renderer
        this.plot = new PlotRenderer(this);
        this.experiences = new DimensionExperiences(this);

        // Load dimension metadata before URL handling so the selector is populated dynamically
        await this.loadDimensionCatalog();

        // Set up URL management after the dimension selector exists
        this.setupURLManagement();

        // Initialize plot
        this.plot.initPlot();

        // Set up zoom after plot is initialized
        this.setupZoom();
        this.setupZoomControls();
        this.setupStickyTopAxis();

        // Load initial dimension
        await this.loadDimension(this.currentDimension);

        // Load exchange rates for cost dimension
        await this.loadExchangeRates();
    }

    async loadDimensionCatalog() {
        try {
            const response = await fetch('exports/json/dimension_catalog.json');
            if (!response.ok) {
                return;
            }
            const catalog = await response.json();
            if (!Array.isArray(catalog) || catalog.length === 0) {
                return;
            }
            this.dimensionCatalog = catalog;
            this.dimensionCatalogBySlug = new Map(catalog.map(entry => [entry.slug, entry]));
            this.populateDimensionSelector(catalog);
            this.renderDimensionBrowser(catalog);
            this.updateDimensionToggleLabel();
        } catch (error) {
            console.warn('Falling back to static dimension selector:', error);
        }
    }

    getAvailableDimensionEntries(catalog) {
        return (catalog || [])
            .filter(entry => entry.available)
            .sort((a, b) => {
                const orderCompare = (a.frontend_order || 1000) - (b.frontend_order || 1000);
                if (orderCompare !== 0) return orderCompare;
                return (a.name || '').localeCompare(b.name || '');
            });
    }

    populateDimensionSelector(catalog) {
        const available = this.getAvailableDimensionEntries(catalog);

        if (available.length === 0) {
            return;
        }

        const groups = new Map();
        for (const entry of available) {
            const groupLabel = entry.frontend_group_label || 'Other';
            if (!groups.has(groupLabel)) {
                groups.set(groupLabel, []);
            }
            groups.get(groupLabel).push(entry);
        }

        this.dimensionSelect.innerHTML = '';
        for (const [groupLabel, entries] of groups.entries()) {
            const optgroup = document.createElement('optgroup');
            optgroup.label = groupLabel;
            for (const entry of entries) {
                const option = document.createElement('option');
                option.value = entry.slug;
                option.textContent = entry.name;
                optgroup.appendChild(option);
            }
            this.dimensionSelect.appendChild(optgroup);
        }
    }

    renderDimensionBrowser(catalog) {
        if (!this.dimensionBrowser) return;

        const available = this.getAvailableDimensionEntries(catalog);

        const groups = new Map();
        for (const entry of available) {
            const groupLabel = entry.frontend_group_label || 'Other';
            if (!groups.has(groupLabel)) {
                groups.set(groupLabel, []);
            }
            groups.get(groupLabel).push(entry);
        }

        this.dimensionBrowser.innerHTML = '';

        const columnCount = this.getDimensionBrowserColumnCount();
        this.dimensionBrowser.style.setProperty('--dimension-browser-columns', String(columnCount));

        const columns = Array.from({ length: columnCount }, () => {
            const column = document.createElement('div');
            column.className = 'dimension-browser__column';
            this.dimensionBrowser.appendChild(column);
            return column;
        });
        const columnHeights = new Array(columnCount).fill(0);

        for (const [groupLabel, entries] of groups.entries()) {
            const group = document.createElement('section');
            group.className = 'dimension-browser__group';
            group.dataset.groupLabel = groupLabel.toLowerCase();
            group.dataset.itemCount = String(entries.length);
            if (entries.length <= 3) {
                group.classList.add('dimension-browser__group--small');
            } else if (entries.length <= 6) {
                group.classList.add('dimension-browser__group--medium');
            } else {
                group.classList.add('dimension-browser__group--large');
            }

            const title = document.createElement('h3');
            title.className = 'dimension-browser__group-title';
            title.textContent = groupLabel;
            group.appendChild(title);

            const chips = document.createElement('div');
            chips.className = 'dimension-browser__chips';
            for (const entry of entries) {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'dimension-chip';
                button.dataset.dimension = entry.slug;
                button.dataset.searchText = String(entry.name || '').toLowerCase();
                button.textContent = entry.name;
                button.addEventListener('click', async () => {
                    await this.setDimension(entry.slug);
                });
                chips.appendChild(button);
            }

            group.appendChild(chips);

            const shortestColumnIndex = columnHeights.indexOf(Math.min(...columnHeights));
            columns[shortestColumnIndex].appendChild(group);
            columnHeights[shortestColumnIndex] += entries.length + 1.6;
        }

        this.updateDimensionBrowserSelection();
        this.filterDimensionBrowser(this.dimensionBrowserSearch?.value || '');
    }

    getDimensionBrowserColumnCount() {
        const width = window.innerWidth || document.documentElement.clientWidth || 0;
        if (width <= 760) return 1;
        if (width <= 1180) return 2;
        return 3;
    }

    setDimensionBrowserOpen(isOpen) {
        this.isDimensionBrowserOpen = Boolean(isOpen);
        if (this.dimensionBrowserPanel) {
            this.dimensionBrowserPanel.hidden = !this.isDimensionBrowserOpen;
        }
        if (this.dimensionBrowserToggle) {
            this.dimensionBrowserToggle.setAttribute('aria-expanded', this.isDimensionBrowserOpen ? 'true' : 'false');
            this.dimensionBrowserToggle.classList.toggle('is-open', this.isDimensionBrowserOpen);
        }
        if (!this.isDimensionBrowserOpen && this.dimensionBrowserSearch) {
            this.dimensionBrowserSearch.value = '';
            this.filterDimensionBrowser('');
        }
        if (this.isDimensionBrowserOpen && this.dimensionBrowserSearch) {
            window.setTimeout(() => this.dimensionBrowserSearch.focus(), 0);
        }
    }

    toggleDimensionBrowser(forceState = null) {
        const nextState = forceState === null ? !this.isDimensionBrowserOpen : Boolean(forceState);
        this.setDimensionBrowserOpen(nextState);
    }

    renderUnitBrowser(visibleUnits) {
        if (!this.unitBrowserList) return;
        this.unitBrowserList.innerHTML = '';
        for (const { unit } of visibleUnits) {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'unit-chip';
            button.dataset.unitName = unit.name;
            const unitNameCapitalized = unit.name.charAt(0).toUpperCase() + unit.name.slice(1);
            const unitLatex = this.unitSymbolToLatex(unit.symbol);
            button.innerHTML = `
                <span class="unit-chip__name">${this.escapeHtml(unitNameCapitalized)}</span>
                <span class="unit-chip__symbol">\\(${this.escapeHtml(unitLatex)}\\)</span>
            `;
            button.addEventListener('click', () => this.setCurrentUnit(unit.name));
            this.unitBrowserList.appendChild(button);
        }
        this.typesetMathIfReady(this.unitBrowserList);
    }

    updateUnitBrowserSelection() {
        if (!this.unitBrowserList) return;
        this.unitBrowserList.querySelectorAll('.unit-chip').forEach(button => {
            button.classList.toggle('is-active', button.dataset.unitName === this.currentUnit);
        });
    }

    updateUnitToggleLabel() {
        if (!this.unitBrowserCurrent || !this.dimensionData?.units) return;
        const unit = this.dimensionData.units.find(entry => entry.name === this.currentUnit);
        if (!unit) return;
        const unitNameCapitalized = unit.name.charAt(0).toUpperCase() + unit.name.slice(1);
        const unitLatex = this.unitSymbolToLatex(unit.symbol);
        this.unitBrowserCurrent.innerHTML = `
            <span class="unit-browser-current__name">${this.escapeHtml(unitNameCapitalized)}</span>
            <span class="unit-browser-current__symbol">\\(${this.escapeHtml(unitLatex)}\\)</span>
        `;
        this.typesetMathIfReady(this.unitBrowserCurrent);
    }

    setUnitBrowserOpen(isOpen) {
        this.isUnitBrowserOpen = Boolean(isOpen);
        if (this.unitBrowserPanel) {
            this.unitBrowserPanel.hidden = !this.isUnitBrowserOpen;
        }
        if (this.unitBrowserToggle) {
            this.unitBrowserToggle.setAttribute('aria-expanded', this.isUnitBrowserOpen ? 'true' : 'false');
            this.unitBrowserToggle.classList.toggle('is-open', this.isUnitBrowserOpen);
        }
    }

    toggleUnitBrowser(forceState = null) {
        const nextState = forceState === null ? !this.isUnitBrowserOpen : Boolean(forceState);
        this.setUnitBrowserOpen(nextState);
    }

    setCurrentUnit(unitName, { closePicker = true } = {}) {
        this.hideUnitConversions();
        this.currentUnit = unitName;
        if (this.unitSelect) {
            this.unitSelect.value = unitName;
        }
        this.updateUnitDescription();
        this.updateUnitBrowserSelection();
        this.updateUnitToggleLabel();
        this.updateURL();
        this.plot.lastTickSet = null;
        this.plot.lastTickDomain = null;
        this.plot.lastTickLogRange = null;
        this.plot.updatePlot();
        if (this.tooltip?.classList.contains('visible') && this.tooltipItem) {
            const value = this.tooltip.querySelector('.tooltip-value');
            value.innerHTML = this.formatTooltipValueHTML(
                this.formatValueForCurrentUnit(this.tooltipItem.value, 2, true),
                this.getCurrentUnitDefinition()?.symbol || '');
            this.enableUnitConversions(value, this.tooltipItem.value);
        }
        if (closePicker) {
            this.setUnitBrowserOpen(false);
        }
    }

    updateDimensionToggleLabel() {
        if (!this.dimensionBrowserCurrent) return;
        const currentEntry = this.dimensionCatalogBySlug.get(this.currentDimension);
        this.dimensionBrowserCurrent.textContent = currentEntry?.name || this.currentDimension;
    }

    updateDimensionBrowserSelection() {
        if (!this.dimensionBrowser) return;
        this.dimensionBrowser.querySelectorAll('.dimension-chip').forEach(button => {
            button.classList.toggle('is-active', button.dataset.dimension === this.currentDimension);
        });
    }

    filterDimensionBrowser(rawQuery) {
        if (!this.dimensionBrowser) return;

        const query = String(rawQuery || '').trim().toLowerCase();
        let visibleGroupCount = 0;
        let visibleChipCount = 0;

        this.dimensionBrowser.querySelectorAll('.dimension-browser__group').forEach(group => {
            let groupVisibleChipCount = 0;

            group.querySelectorAll('.dimension-chip').forEach(button => {
                const matches = !query || (button.dataset.searchText || '').includes(query);
                button.hidden = !matches;
                if (matches) {
                    groupVisibleChipCount += 1;
                    visibleChipCount += 1;
                }
            });

            group.hidden = groupVisibleChipCount === 0;
            if (!group.hidden) {
                visibleGroupCount += 1;
            }
        });

        if (this.dimensionBrowserEmpty) {
            this.dimensionBrowserEmpty.hidden = visibleChipCount !== 0;
        }

        this.dimensionBrowser.hidden = visibleGroupCount === 0;
    }

    async setDimension(slug) {
        this.experiences?.pause();
        this.hideTooltip();
        this.currentDimension = slug;
        if (this.dimensionSelect) {
            this.dimensionSelect.value = slug;
        }
        this.updateDimensionBrowserSelection();
        this.updateDimensionToggleLabel();
        this.setDimensionBrowserOpen(false);
        await this.loadDimension(slug);
        this.updateURL();
    }

    setupEventListeners() {
        this.dimensionSelect.addEventListener('change', async (e) => {
            await this.setDimension(e.target.value);
        });

        if (this.dimensionBrowserToggle) {
            this.dimensionBrowserToggle.addEventListener('click', (event) => {
                event.stopPropagation();
                this.toggleDimensionBrowser();
            });
        }

        if (this.dimensionBrowserSearch) {
            this.dimensionBrowserSearch.addEventListener('input', (event) => {
                this.filterDimensionBrowser(event.target.value);
            });
            this.dimensionBrowserSearch.addEventListener('search', (event) => {
                this.filterDimensionBrowser(event.target.value);
            });
        }

        window.addEventListener('resize', () => {
            clearTimeout(this.dimensionBrowserResizeTimer);
            this.dimensionBrowserResizeTimer = window.setTimeout(() => {
                if (this.dimensionCatalog?.length) {
                    this.renderDimensionBrowser(this.dimensionCatalog);
                }
            }, 120);
        });

        document.addEventListener('click', (event) => {
            if (this.isDimensionBrowserOpen) {
                const clickedInsideDimensionBrowser = this.dimensionBrowserPanel?.contains(event.target);
                const clickedDimensionToggle = this.dimensionBrowserToggle?.contains(event.target);
                if (!clickedInsideDimensionBrowser && !clickedDimensionToggle) {
                    this.setDimensionBrowserOpen(false);
                }
            }
            if (this.isUnitBrowserOpen) {
                const clickedInsideUnitBrowser = this.unitBrowserPanel?.contains(event.target);
                const clickedUnitToggle = this.unitBrowserToggle?.contains(event.target);
                if (!clickedInsideUnitBrowser && !clickedUnitToggle) {
                    this.setUnitBrowserOpen(false);
                }
            }
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && this.isDimensionBrowserOpen) {
                this.setDimensionBrowserOpen(false);
            }
            if (event.key === 'Escape' && this.isUnitBrowserOpen) {
                this.setUnitBrowserOpen(false);
            }
        });

        this.unitSelect.addEventListener('change', (e) => {
            this.setCurrentUnit(e.target.value, { closePicker: false });
        });

        if (this.unitBrowserToggle) {
            this.unitBrowserToggle.addEventListener('click', (event) => {
                event.stopPropagation();
                this.toggleUnitBrowser();
            });
        }

        this.darkModeToggle.addEventListener('click', () => {
            this.toggleDarkMode();
        });

        this.musicToggle.addEventListener('click', () => {
            this.toggleMusic();
        });

        this.notationToggle.addEventListener('click', () => {
            this.toggleNotation();
        });

        if (this.resourcesToggle) {
            this.resourcesToggle.addEventListener('click', () => {
                this.toggleResources();
            });
        }

        // Hide tooltips when clicking elsewhere (but allow clicks on tooltip itself)
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.plot-item') && !e.target.closest('.label-hover-area') &&
                !e.target.closest('.tooltip') && !e.target.closest('.image-modal') &&
                !e.target.closest('.unit-value-trigger') && !e.target.closest('.unit-conversions-popover')) {
                this.hideTooltip();
            }
        });

        // Set up image modal event listeners
        if (this.imageModal) {
            const backdrop = this.imageModal.querySelector('.image-modal-backdrop');
            if (backdrop) {
                backdrop.addEventListener('click', () => this.closeImageModal());
            }
            if (this.imageModalClose) {
                this.imageModalClose.addEventListener('click', () => this.closeImageModal());
            }
            // Close on Escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.imageModal?.classList.contains('active')) {
                    this.closeImageModal();
                }
            });
        }

        // Handle window resize with debouncing to prevent zoom reset on mobile scroll
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.plot.updateDimensions();
                this.resizePlot();
            }, CONFIG.RESIZE_DEBOUNCE_MS);
        });

    }

    initDarkMode() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        this.updateDarkModeButton(savedTheme);
    }

    recordImageFailure(url) {
        if (!url) return;
        if (!this.failedUrls) this.failedUrls = new Set();
        this.failedUrls.add(url);
    }

    initNotation() {
        const savedMode = localStorage.getItem('notationMode') || 'scientific';
        this.notationMode = savedMode;
        this.formatter.setNotationMode(savedMode);

        // Update button text to show current mode
        this.updateNotationButton();
    }

    updateNotationButton() {
        if (this.usesLinearDisplayValues()) {
            this.notationToggle.textContent = '123';
            this.notationToggle.disabled = true;
            this.notationToggle.classList.add('notation-toggle--disabled');
            this.notationToggle.title = 'This view uses regular numeric labels.';
            return;
        }

        this.notationToggle.disabled = false;
        this.notationToggle.classList.remove('notation-toggle--disabled');
        this.notationToggle.title = 'Toggle number notation';
        if (this.notationMode === 'mathematical') {
            // For mathematical notation, use HTML with superscript
            this.notationToggle.innerHTML = '1×10<sup>10</sup>';
        } else {
            // For other modes, use plain text
            this.notationToggle.textContent = CONFIG.NOTATION_BUTTON_TEXTS[this.notationMode];
        }
    }

    toggleDarkMode() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);

        this.updateDarkModeButton(newTheme);

        // Update plot colors
        this.plot.updatePlotColors();
    }

    updateDarkModeButton(theme) {
        this.darkModeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
    }

    toggleMusic() {
        this.experiences?.audio.stop();
        // Remove enableAudio listeners if they exist (user is explicitly toggling)
        if (this.enableAudioHandler) {
            document.removeEventListener('click', this.enableAudioHandler);
            document.removeEventListener('keydown', this.enableAudioHandler);
            document.removeEventListener('touchstart', this.enableAudioHandler);
            this.enableAudioHandler = null;
        }

        if (this.backgroundMusic.paused) {
            this.backgroundMusic.play().catch(e => {
                console.log('Audio play failed:', e);
                // Some browsers require user interaction before playing audio
            });
            this.musicToggle.classList.add('playing');
            this.musicToggle.textContent = '🔊';
            // Save music state to localStorage
            localStorage.setItem('musicEnabled', 'true');
        } else {
            this.backgroundMusic.pause();
            this.musicToggle.classList.remove('playing');
            this.musicToggle.textContent = '🎵';
            // Save music state to localStorage
            localStorage.setItem('musicEnabled', 'false');
        }
    }

    toggleNotation() {
        if (this.usesLinearDisplayValues()) {
            return;
        }
        const modes = ['scientific', 'mathematical', 'human'];
        const currentIndex = modes.indexOf(this.notationMode);
        this.notationMode = modes[(currentIndex + 1) % modes.length];
        this.formatter.setNotationMode(this.notationMode);

        // Update button text to show current mode
        this.updateNotationButton();

        // Save to localStorage
        localStorage.setItem('notationMode', this.notationMode);

        // Update plot to reflect new notation
        this.experiences?.refresh();
        this.plot.updatePlotAfterZoom();
    }

    formatNumber(value, precision = 0, forTooltip = false) {
        if (this.isLinearScale()) {
            return this.formatter.formatLinearNumber(value, Math.max(precision, forTooltip ? 2 : 0));
        }
        return this.formatter.formatNumber(value, precision, forTooltip);
    }

    formatMathematicalHTML(sign, mantissa, exponent) {
        return this.formatter.formatMathematicalHTML(sign, mantissa, exponent);
    }

    formatHumanReadable(value, precision = 2) {
        return this.formatter.formatHumanReadable(value, precision);
    }

    processMathematicalLabels(axis) {
        this.formatter.processMathematicalLabels(axis);
    }

    getScaleMode() {
        return this.dimensionData?.scale_mode === 'linear' ? 'linear' : 'log';
    }

    isLinearScale() {
        return this.getScaleMode() === 'linear';
    }

    usesLinearDisplayValues() {
        return this.isLinearScale() || this.isSoundIntensityDecibelUnit();
    }

    isSoundIntensityDecibelUnit(unit = null) {
        const resolvedUnit = unit || this.getCurrentUnitDefinition();
        return this.currentDimension === 'sound-intensity'
            && resolvedUnit?.special_conversion === 'sound_intensity_db';
    }

    getCurrentUnitDefinition() {
        return this.dimensionData?.units?.find(unit => unit.name === this.currentUnit) || null;
    }

    getAvailableUnits() {
        return (this.dimensionData?.units || []).filter((unit, index) =>
            !this.editor?.unitOverrides?.[this.currentDimension]?.[index]?.isDeleted &&
            this.isUnitCompatibleWithCurrentScale(unit));
    }

    formatValueInUnit(value, unit) {
        const converted = unit.special_conversion === 'sound_intensity_db'
            ? (value > 0 ? 10 * Math.log10(value / 1e-12) : Number.NEGATIVE_INFINITY)
            : this.convertBaseValueToUnit(value, unit);
        return unit.special_conversion === 'sound_intensity_db'
            ? this.formatter.formatLinearNumber(converted, 2)
            : this.formatNumber(converted, 2, true);
    }

    formatValueInUnitHTML(value, unit) {
        const formatted = this.formatValueInUnit(value, unit);
        const valueHtml = !this.isLinearScale() && this.notationMode === 'mathematical' &&
            unit.special_conversion !== 'sound_intensity_db'
            ? formatted : this.escapeHtml(formatted);
        const symbolHtml = this.formatUnitSymbolHTML(unit.symbol);
        return symbolHtml ? `${valueHtml} ${symbolHtml}` : valueHtml;
    }

    cancelTooltipHide() {
        clearTimeout(this.tooltipHideTimer);
        this.tooltipHideTimer = null;
    }

    scheduleTooltipHide() {
        this.cancelTooltipHide();
        this.tooltipHideTimer = setTimeout(() => {
            if (!this.tooltipPinned && !this.unitPopoverSelecting && !this.isNearUnitConversions())
                this.hideTooltip();
        }, 220);
    }

    isNearUnitConversions() {
        if (!this.unitPopover) return false;
        if (this.unitPopoverSelecting || document.activeElement === this.unitPopoverTrigger) return true;
        const pointer = this.unitPopoverPointer;
        if (!pointer) return false;
        const near = element => {
            if (!element?.isConnected) return false;
            const rect = element.getBoundingClientRect();
            return pointer.x >= rect.left - 24 && pointer.x <= rect.right + 24 &&
                pointer.y >= rect.top - 24 && pointer.y <= rect.bottom + 24;
        };
        return near(this.unitPopover) || near(this.unitPopoverTrigger);
    }

    hideUnitConversions() {
        clearTimeout(this.unitPopoverTimer);
        this.unitPopoverTimer = null;
        if (this.unitPopoverPointerMove) document.removeEventListener('pointermove', this.unitPopoverPointerMove);
        if (this.unitPopoverPointerUp) document.removeEventListener('pointerup', this.unitPopoverPointerUp);
        this.unitPopoverPointerMove = this.unitPopoverPointerUp = null;
        this.unitPopoverSelecting = false;
        this.unitPopover?.remove();
        this.unitPopover = null;
        this.unitPopoverTrigger = null;
    }

    scheduleUnitConversionsHide() {
        clearTimeout(this.unitPopoverTimer);
        this.unitPopoverTimer = setTimeout(() => {
            if (!this.isNearUnitConversions()) this.hideUnitConversions();
        }, 450);
    }

    showUnitConversions(anchor, baseValue) {
        const units = this.getAvailableUnits().filter(unit => unit.name !== this.currentUnit);
        if (!units.length || !anchor.isConnected) return;
        this.hideUnitConversions();
        this.cancelTooltipHide();
        const popover = document.createElement('div');
        popover.className = 'unit-conversions-popover';
        popover.setAttribute('role', 'tooltip');
        popover.innerHTML = `<strong>Other units</strong><div class="unit-conversions-popover__list">${units.map(unit =>
            `<div class="unit-conversions-popover__row"><span>${this.escapeHtml(unit.name)}</span>` +
            `<span>${this.formatValueInUnitHTML(baseValue, unit)}</span></div>`
        ).join('')}</div>`;
        popover.addEventListener('pointerenter', () => {
            clearTimeout(this.unitPopoverTimer);
            this.cancelTooltipHide();
        });
        popover.addEventListener('pointerleave', () => {
            this.scheduleUnitConversionsHide();
            if (!this.tooltipPinned && this.tooltip.contains(anchor)) this.scheduleTooltipHide();
        });
        document.body.append(popover);
        this.unitPopover = popover;
        this.unitPopoverTrigger = anchor;
        this.unitPopoverPointerMove = event => {
            this.unitPopoverPointer = { x: event.clientX, y: event.clientY };
            if (this.isNearUnitConversions()) {
                clearTimeout(this.unitPopoverTimer);
                this.cancelTooltipHide();
            } else this.scheduleUnitConversionsHide();
        };
        this.unitPopoverPointerUp = () => {
            this.unitPopoverSelecting = false;
            if (!this.isNearUnitConversions()) this.scheduleUnitConversionsHide();
        };
        popover.addEventListener('pointerdown', () => {
            this.unitPopoverSelecting = true;
            clearTimeout(this.unitPopoverTimer);
            this.cancelTooltipHide();
        });
        document.addEventListener('pointermove', this.unitPopoverPointerMove, { passive: true });
        document.addEventListener('pointerup', this.unitPopoverPointerUp);
        const rect = anchor.getBoundingClientRect();
        const width = popover.getBoundingClientRect().width;
        popover.style.left = `${Math.max(8, Math.min(rect.left, innerWidth - width - 8))}px`;
        const height = popover.getBoundingClientRect().height;
        popover.style.top = `${rect.bottom + height + 8 < innerHeight ? rect.bottom + 6 :
            Math.max(8, rect.top - height - 6)}px`;
        this.typesetMathIfReady(popover);
    }

    enableUnitConversions(anchor, baseValue) {
        anchor.classList.remove('unit-value-trigger');
        anchor.removeAttribute('role');
        anchor.removeAttribute('aria-label');
        anchor.removeAttribute('tabindex');
        anchor.onpointerenter = anchor.onpointerleave = anchor.onfocus = anchor.onblur = null;
        anchor.onkeydown = anchor.onclick = null;
        if (this.getAvailableUnits().length < 2) return;
        anchor.classList.add('unit-value-trigger');
        anchor.tabIndex = 0;
        anchor.setAttribute('role', 'button');
        anchor.setAttribute('aria-label', 'Show this value in other units');
        anchor.onpointerenter = event => {
            this.unitPopoverPointer = { x: event.clientX, y: event.clientY };
            this.showUnitConversions(anchor, baseValue);
        };
        anchor.onpointerleave = () => this.scheduleUnitConversionsHide();
        anchor.onfocus = () => this.showUnitConversions(anchor, baseValue);
        anchor.onblur = () => this.scheduleUnitConversionsHide();
        anchor.onkeydown = event => {
            if (event.key === 'Escape') this.hideUnitConversions();
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                this.showUnitConversions(anchor, baseValue);
            }
        };
        anchor.onclick = event => {
            event.stopPropagation();
            this.showUnitConversions(anchor, baseValue);
        };
    }

    convertBaseValueToUnit(valueBase, unit) {
        if (!unit) return Number(valueBase);
        const factor = Number(unit.conversion_factor ?? 1);
        const offset = Number(unit.offset ?? 0);
        if (!Number.isFinite(factor) || !Number.isFinite(offset)) return Number.NaN;
        return Number(valueBase) * factor + offset;
    }

    isUnitCompatibleWithCurrentScale(unit) {
        if (!unit) return false;
        if (this.isLinearScale()) return true;
        if (unit.special_conversion) return true;
        if (!Array.isArray(this.dimensionData?.items) || this.dimensionData.items.length === 0) return true;

        for (const item of this.dimensionData.items) {
            const baseValue = Number(item?.value);
            if (!Number.isFinite(baseValue) || baseValue <= 0) continue;
            const converted = this.convertBaseValueToUnit(baseValue, unit);
            if (!Number.isFinite(converted) || converted <= 0) {
                return false;
            }
        }
        return true;
    }

    isDomainZoomed(currentDomain, originalDomain) {
        if (!currentDomain || !originalDomain) return false;
        const delta = Math.max(
            Math.abs(currentDomain[0] - originalDomain[0]),
            Math.abs(currentDomain[1] - originalDomain[1])
        );
        const scale = Math.max(
            Math.abs(originalDomain[0]),
            Math.abs(originalDomain[1]),
            Math.abs(originalDomain[1] - originalDomain[0]),
            1
        );
        return (delta / scale) > CONFIG.ZOOM_DETECTION_THRESHOLD;
    }

    initMusic() {
        // Load saved music state from localStorage
        // Default to true (music on) if no saved state exists
        const savedMusicState = localStorage.getItem('musicEnabled');
        const musicWasEnabled = savedMusicState === null || savedMusicState === 'true';

        if (musicWasEnabled) {
            // Music should be on - set button state to "on"
            this.musicToggle.classList.add('playing');
            this.musicToggle.textContent = '🔊';

            // Try to play immediately - this will likely fail due to browser restrictions
            this.backgroundMusic.play().catch(e => {
                console.log('Autoplay blocked by browser:', e);
                // This is expected - we'll wait for user interaction
            });

            // Add click listener to any element to enable audio on first interaction
            this.enableAudioOnInteraction(true);
        } else {
            // Music was explicitly turned off - set button state to "off"
            this.musicToggle.classList.remove('playing');
            this.musicToggle.textContent = '🎵';
            // Don't try to autoplay
        }
    }

    enableAudioOnInteraction(shouldPlay = false) {
        const enableAudio = (event) => {
            // Don't handle clicks on the music toggle button - let toggleMusic handle it
            if (event.target === this.musicToggle || this.musicToggle.contains(event.target)) {
                return;
            }

            // Only try to play if music should be enabled and is not already playing
            if (shouldPlay && this.backgroundMusic.paused) {
                this.backgroundMusic.play().then(() => {
                    // Button state should already be correct, but ensure it is
                    this.musicToggle.classList.add('playing');
                    this.musicToggle.textContent = '🔊';
                }).catch(e => {
                    console.log('Play failed:', e);
                });
            }
            // Remove listeners after first successful interaction
            document.removeEventListener('click', enableAudio);
            document.removeEventListener('keydown', enableAudio);
            document.removeEventListener('touchstart', enableAudio);
            this.enableAudioHandler = null;
        };

        // Store reference for cleanup
        this.enableAudioHandler = enableAudio;

        // Listen for any user interaction
        document.addEventListener('click', enableAudio);
        document.addEventListener('keydown', enableAudio);
        document.addEventListener('touchstart', enableAudio);
    }

    setupURLManagement() {
        const urlParams = new URLSearchParams(window.location.search);
        const dimension = urlParams.get('dimension');
        if (dimension && this.dimensionSelect.querySelector(`option[value="${dimension}"]`)) {
            this.currentDimension = dimension;
            this.dimensionSelect.value = dimension;
        }

        // Store unit parameter to use after dimension loads
        const unit = urlParams.get('unit');
        if (unit) {
            this.pendingUnit = unit;
        }

        // Handle hash-based data sharing
        this.loadSharedDataFromURL();
    }

    loadSharedDataFromURL() {
        const hash = window.location.hash;
        if (hash.startsWith('#data=')) {
            try {
                const compressedData = hash.substring(6);
                const decompressedData = LZString.decompressFromEncodedURIComponent(compressedData);
                if (decompressedData) {
                    const parsedData = JSON.parse(decompressedData);

                    // Merge into customItems
                    if (parsedData.customItems) {
                        // Special handling to merge by dimension
                        for (const dim in parsedData.customItems) {
                            this.customItems[dim] = parsedData.customItems[dim];
                        }
                    }

                    if (this.editor) {
                        if (parsedData.dimensionOverrides) {
                            this.editor.dimensionOverrides = { ...this.editor.dimensionOverrides, ...parsedData.dimensionOverrides };
                        }
                        if (parsedData.unitOverrides) {
                            this.editor.unitOverrides = { ...this.editor.unitOverrides, ...parsedData.unitOverrides };
                        }
                    }

                    console.log('✅ Custom scale data loaded from link');

                    // Trigger a re-render of current dimension if it's already loaded
                    if (this.dimensionData) {
                        this.plot.updatePlot();
                        if (this.editor) {
                            this.editor.onDimensionChange();
                        }
                    }
                }
            } catch (e) {
                console.error('Failed to load shared data from link:', e);
            }
        }
    }

    updateURL() {
        const url = new URL(window.location);
        url.searchParams.set('dimension', this.currentDimension);
        if (this.currentUnit) {
            url.searchParams.set('unit', this.currentUnit);
        } else {
            url.searchParams.delete('unit');
        }
        window.history.pushState({}, '', url);
    }

    async loadDimension(dimension) {
        const requestId = this.dimensionRequestId = (this.dimensionRequestId || 0) + 1;
        try {
            let response = await fetch(`exports/frontend/${dimension}.yaml`);
            if (!response.ok) {
                response = await fetch(`data/${dimension}.yaml`);
            }
            if (!response.ok) {
                throw new Error(`Missing dimension payload for ${dimension}`);
            }
            const yamlText = await response.text();
            if (requestId !== this.dimensionRequestId) return;
            this.dimensionData = jsyaml.load(yamlText);
            this.normalizeDimensionUnitSymbols();
            if (dimension === 'sound-intensity' && Array.isArray(this.dimensionData.units)) {
                const existingDecibelUnit = this.dimensionData.units.find(unit => unit.name === 'decibels');
                if (existingDecibelUnit) {
                    existingDecibelUnit.special_conversion = 'sound_intensity_db';
                } else {
                    this.dimensionData.units.push({
                        name: 'decibels',
                        symbol: 'dB',
                        conversion_factor: 1.0,
                        description: 'Decibel sound level, referenced to $10^{-12}\\,\\mathrm{W/m^2}$. The plot spacing still comes from physical intensity, but the labels are shown in the more familiar loudness scale.',
                        special_conversion: 'sound_intensity_db'
                    });
                }
            }

            // Fully reset zoom state when dimension changes so new plots start zoomed out
            this.originalXDomain = null;
            this.actualItemExtent = null;
            if (this.zoomBehavior && this.mainGroup) {
                // Immediately reset transform to identity (no animation) so updatePlot
                // can establish a fresh domain based on the new dimension data
                this.mainGroup.interrupt();
                this.mainGroup.call(this.zoomBehavior.transform, d3.zoomIdentity);
            }


            // Reset tick cache when dimension changes
            this.plot.lastTickSet = null;
            this.plot.lastTickDomain = null;
            this.plot.lastTickLogRange = null;

            // Update dimension description (check for overrides)
            const dimensionDescOverride = this.editor?.dimensionOverrides[this.currentDimension]?.description;
            const dimensionDesc = dimensionDescOverride !== undefined
                ? dimensionDescOverride
                : (this.dimensionData.dimension_description || '');

            if (dimensionDesc) {
                this.setRichText(this.dimensionDescription, dimensionDesc);
                this.dimensionDescription.style.display = '';
            } else {
                this.dimensionDescription.textContent = '';
                this.dimensionDescription.style.display = 'none'; // Hide when empty
            }

            // Update Related Resources
            this.updateRelatedResources();

            // Update Limitations Note visibility
            const limitationsNote = document.getElementById('limitations-note');
            if (limitationsNote) {
                limitationsNote.style.display = this.dimensionData.show_limitations !== false ? 'block' : 'none';
            }

            // Update unit selector
            this.updateUnitSelector();
            this.updateNotationButton();
            this.updateDimensionBrowserSelection();
            this.updateDimensionToggleLabel();

            this.experiences?.onDimension();

            // Update plot
            this.plot.updatePlot();

            // Update sticky top axis after plot update
            if (this.updateStickyAxis) {
                this.updateStickyAxis();
            }

            // Update plot colors based on current theme
            this.plot.updatePlotColors();


            // Refresh editor if it's open
            if (this.editor) {
                this.editor.onDimensionChange();
            }

        } catch (error) {
            if (requestId !== this.dimensionRequestId) return;
            console.error('Error loading dimension:', error);
            this.showError(`Failed to load ${dimension} data`);
        }
    }

    normalizeDimensionUnitSymbols() {
        if (!Array.isArray(this.dimensionData?.units)) return;
        this.dimensionData.units.forEach((unit) => {
            if (!unit) return;
            unit.symbol = this.normalizeMicroPrefixSymbol(unit.symbol, unit.name);
        });
    }

    normalizeMicroPrefixSymbol(symbol, unitName) {
        if (!symbol) return symbol;
        const name = String(unitName || '').toLowerCase();
        let normalized = String(symbol).trim();

        normalized = normalized.replace(/\\mu\s*/g, 'μ');

        if (!name.includes('micro')) {
            return normalized;
        }

        normalized = normalized.replace(/^u(?=[A-Za-z])/g, 'μ');
        normalized = normalized.replace(/([/(\[])\s*u(?=[A-Za-z])/g, '$1μ');
        normalized = normalized.replace(/\bu(?=[A-Za-z])/g, 'μ');
        return normalized;
    }

    updateUnitSelector() {
        this.unitSelect.innerHTML = '';

        // Filter out deleted units
        const visibleUnits = [];
        if (this.editor && this.editor.unitOverrides[this.currentDimension]) {
            this.dimensionData.units.forEach((unit, index) => {
                const isDeleted = this.editor.unitOverrides[this.currentDimension]?.[index]?.isDeleted;
                if (!isDeleted && this.isUnitCompatibleWithCurrentScale(unit)) {
                    visibleUnits.push({ unit, index });
                }
            });
        } else {
            // No overrides, all units are visible
            this.dimensionData.units.forEach((unit, index) => {
                if (this.isUnitCompatibleWithCurrentScale(unit)) {
                    visibleUnits.push({ unit, index });
                }
            });
        }

        visibleUnits.forEach(({ unit }) => {
            const option = document.createElement('option');
            option.value = unit.name;
            // Capitalize first letter for display
            const unitNameCapitalized = unit.name.charAt(0).toUpperCase() + unit.name.slice(1);
            const symbolDisplay = this.formatUnitSymbolDisplayText(unit.symbol);
            option.textContent = `${unitNameCapitalized} (${symbolDisplay})`;
            this.unitSelect.appendChild(option);
        });
        this.renderUnitBrowser(visibleUnits);

        // Set unit from URL if pending, otherwise use first visible unit
        if (this.pendingUnit && visibleUnits.some(({ unit }) => unit.name === this.pendingUnit)) {
            this.currentUnit = this.pendingUnit;
            this.unitSelect.value = this.currentUnit;
            this.pendingUnit = null; // Clear pending unit
        } else if (this.currentDimension === 'sound-intensity' && visibleUnits.some(({ unit }) => unit.name === 'decibels')) {
            this.currentUnit = 'decibels';
            this.unitSelect.value = this.currentUnit;
        } else if (visibleUnits.length > 0) {
            this.currentUnit = visibleUnits[0].unit.name;
            this.unitSelect.value = this.currentUnit;
        }

        // Update unit description
        this.updateUnitDescription();
        this.updateUnitBrowserSelection();
        this.updateUnitToggleLabel();
    }

    updateRelatedResources() {
        const resourcesLinks = document.getElementById('related-resources');
        if (!resourcesLinks || !this.resourcesPanel) return;

        const resources = this.dimensionData.related_resources || [];
        if (resources.length > 0) {
            resourcesLinks.innerHTML = resources.map(res =>
                `<a href="${res.url}" target="_blank" rel="noopener noreferrer">${res.name}</a>`
            ).join('');
            this.resourcesPanel.style.display = 'block';
        } else {
            resourcesLinks.innerHTML = '';
            this.resourcesPanel.style.display = 'none';
        }
    }

    toggleResources() {
        const isExpanded = this.resourcesContent.style.display !== 'none';
        if (isExpanded) {
            this.resourcesContent.style.display = 'none';
            this.resourcesToggle.classList.remove('expanded');
        } else {
            this.resourcesContent.style.display = 'flex';
            this.resourcesContent.style.flexDirection = 'column';
            this.resourcesToggle.classList.add('expanded');
        }
    }

    showTooltip(event, item, pinned = false) {
        this.cancelTooltipHide();
        this.hideUnitConversions();
        this.tooltipItem = item;
        const unit = this.getCurrentUnitDefinition();

        // Determine if this is a touch/mobile device
        const isTouchPrimary = (event && (event.pointerType === 'touch' || event.pointerType === 'pen'))
            || ('ontouchstart' in window)
            || window.matchMedia('(hover: none)').matches;

        // Set pinned state - on mobile, tooltips are always "pinned" (interactive)
        this.tooltipPinned = pinned || isTouchPrimary;

        this.tooltip.querySelector('.tooltip-title').textContent = item.name;

        // Handle image - check if image exists before displaying
        const tooltipImage = this.tooltip.querySelector('.tooltip-image');
        const imagePath = this.getImagePath(item.name);

        // Immediately hide the image and clear src to prevent showing previous image
        tooltipImage.style.display = 'none';
        tooltipImage.src = '';
        tooltipImage.alt = '';
        tooltipImage.draggable = false; // Prevent native image dragging

        // Format and display the exact value (use forTooltip=true to get HTML superscripts in tooltips)
        const formattedValue = this.formatValueForCurrentUnit(item.value, 2, true);
        const unitSymbol = unit ? unit.symbol : '';
        const tooltipValueElement = this.tooltip.querySelector('.tooltip-value');
        tooltipValueElement.innerHTML = this.formatTooltipValueHTML(formattedValue, unitSymbol);
        this.enableUnitConversions(tooltipValueElement, item.value);

        const descriptionElement = this.tooltip.querySelector('.tooltip-description');
        const descriptionText = item.description || item.description_long || item.description_medium || item.summary_short || '';
        const tooltipMarkdown = this.buildTooltipDescriptionMarkdown(item, descriptionText);
        if (tooltipMarkdown) {
            this.setRichText(descriptionElement, tooltipMarkdown);
        } else {
            descriptionElement.textContent = '';
        }
        this.experiences?.addTooltip(item, descriptionElement);
        const sourceLink = this.tooltip.querySelector('.tooltip-source');
        // isTouchPrimary is already defined above
        const showSourceText = isTouchPrimary || pinned; // Show source on mobile or when pinned on desktop
        if (item.source) {
            sourceLink.href = item.source;
            sourceLink.textContent = showSourceText ? 'Source' : '';
            sourceLink.style.display = showSourceText ? 'inline' : 'none';
        } else {
            sourceLink.removeAttribute('href');
            sourceLink.textContent = '';
            sourceLink.style.display = 'none';
        }

        // Position tooltip (will be repositioned after image loads if image exists)
        const positionTooltip = () => {
            if (isTouchPrimary) {
                // Pin tooltip to viewport top center on mobile via CSS class
                this.tooltip.classList.add('mobile-pinned');
                // Clear any previous desktop inline positioning that could push it off-screen
                // But explicitly set position: fixed for mobile to ensure it's positioned relative to viewport
                this.tooltip.style.left = '';
                this.tooltip.style.top = '';
                this.tooltip.style.transform = '';
                this.tooltip.style.position = 'fixed';
                // Enable pointer events on mobile so source link is clickable
                this.tooltip.style.pointerEvents = 'auto';
                // Use CSS variable for z-index (matches --z-tooltip-pinned in styles.css)
                const tooltipZIndex = getComputedStyle(document.documentElement)
                    .getPropertyValue('--z-tooltip-pinned').trim() || '4000';
                this.tooltip.style.zIndex = tooltipZIndex;
            } else {
                // Use viewport coordinates for robust clamping
                const clientX = event.clientX;
                const clientY = event.clientY;

                // Measure tooltip dimensions once (avoid multiple layout recalculations)
                // Use a single measurement by setting display and visibility together
                const wasVisible = this.tooltip.style.display === 'block';
                if (!wasVisible) {
                    this.tooltip.style.display = 'block';
                    this.tooltip.style.visibility = 'hidden';
                    this.tooltip.style.position = 'fixed';
                    this.tooltip.style.left = '-9999px';
                    this.tooltip.style.top = '-9999px';
                }

                // Set maxWidth to full width to measure natural size
                this.tooltip.style.maxWidth = `${CONFIG.TOOLTIP_MAX_WIDTH}px`;

                // Force a single layout calculation by reading dimensions
                const naturalTooltipWidth = this.tooltip.offsetWidth;
                const naturalTooltipHeight = this.tooltip.offsetHeight;

                // Check if tooltip would be cut off on the right when positioned to the right of cursor
                const spaceOnRight = window.innerWidth - clientX - CONFIG.TOOLTIP_OFFSET_X;
                const wouldBeCutOff = spaceOnRight < naturalTooltipWidth;

                // If it would be cut off, move to left of cursor (don't squish)
                // Otherwise, position to the right and potentially reduce width if needed
                let desiredLeftVp;
                let finalTooltipWidth = naturalTooltipWidth;
                let finalTooltipHeight = naturalTooltipHeight;

                if (wouldBeCutOff) {
                    // Position to the left of cursor
                    desiredLeftVp = clientX - naturalTooltipWidth - CONFIG.TOOLTIP_OFFSET_X;
                    // Keep full width - don't squish
                    this.tooltip.style.maxWidth = `${CONFIG.TOOLTIP_MAX_WIDTH}px`;
                } else {
                    // Position to the right of cursor
                    desiredLeftVp = clientX + CONFIG.TOOLTIP_OFFSET_X;
                    // Dynamically cap tooltip width to available space
                    const maxAllowed = Math.max(CONFIG.TOOLTIP_MIN_WIDTH, spaceOnRight);
                    const newMaxWidth = Math.min(CONFIG.TOOLTIP_MAX_WIDTH, maxAllowed);
                    this.tooltip.style.maxWidth = `${newMaxWidth}px`;
                    // Only remeasure if width actually changed
                    if (newMaxWidth < CONFIG.TOOLTIP_MAX_WIDTH) {
                        finalTooltipWidth = this.tooltip.offsetWidth;
                        finalTooltipHeight = this.tooltip.offsetHeight;
                    }
                    // Ensure it doesn't go off the right edge
                    if (desiredLeftVp + finalTooltipWidth > window.innerWidth - CONFIG.TOOLTIP_OFFSET_X) {
                        desiredLeftVp = window.innerWidth - finalTooltipWidth - CONFIG.TOOLTIP_OFFSET_X;
                    }
                }

                // Clamp horizontal position to ensure it doesn't go off the left edge
                const minLeftVp = CONFIG.TOOLTIP_OFFSET_X;
                desiredLeftVp = Math.max(minLeftVp, desiredLeftVp);

                // Default vertical position: below cursor
                let desiredTopVp = clientY + CONFIG.TOOLTIP_OFFSET_Y;

                // Clamp vertical position to keep tooltip within viewport
                const minTopVp = CONFIG.TOOLTIP_MIN_TOP;
                const maxTopVp = window.innerHeight - CONFIG.TOOLTIP_VIEWPORT_BOTTOM_MARGIN - finalTooltipHeight;
                desiredTopVp = Math.max(minTopVp, Math.min(maxTopVp, desiredTopVp));

                // Apply all styles at once to minimize layout recalculations
                this.tooltip.style.left = `${desiredLeftVp}px`;
                this.tooltip.style.top = `${desiredTopVp}px`;
                this.tooltip.style.position = 'fixed';
                this.tooltip.style.transform = '';
                // Enable pointer events when pinned so source link is clickable
                // Also increase z-index when pinned to ensure it's on top
                this.tooltip.style.pointerEvents = 'auto';
                // Use CSS variable for z-index (matches --z-tooltip-pinned in styles.css)
                const tooltipZIndex = getComputedStyle(document.documentElement)
                    .getPropertyValue('--z-tooltip-pinned').trim() || '4000';
                this.tooltip.style.zIndex = tooltipZIndex;
                if (!wasVisible) {
                    this.tooltip.style.visibility = '';
                }
            }
        };

        // Position tooltip initially
        positionTooltip();

        // Handle image loading - reposition tooltip after image loads to account for image height
        if (imagePath) {
            // Check if image exists before setting src (use thumbnail by default)
            this.checkImageExists(imagePath, true).then(imageInfo => {
                if (imageInfo) {
                    const imageSrc = typeof imageInfo === 'string' ? imageInfo : imageInfo.path;
                    const isThumbnail = typeof imageInfo === 'object' && imageInfo.isThumbnail;
                    const fullImagePath = typeof imageInfo === 'object' ? imageInfo.fullPath : imageInfo;

                    // Debug logging (can be removed in production)
                    if (window.DEBUG_IMAGES) {
                        console.log('Image loading:', { imagePath, imageSrc, isThumbnail, fullImagePath });
                    }

                    // Log image loads to console for visibility
                    console.log(`📷 Loading ${isThumbnail ? 'thumbnail' : 'full'} image: ${imageSrc.split('/').pop()}`);

                    // Create a new image object to preload and only show when loaded
                    const img = new Image();
                    img.onload = () => {
                        // Only set the image if this tooltip is still showing the same item
                        // Check by comparing the current tooltip title
                        if (this.tooltip.querySelector('.tooltip-title').textContent === item.name) {
                            tooltipImage.src = imageSrc;
                            tooltipImage.alt = item.name;
                            tooltipImage.style.display = 'block';

                            // Add click handler to load full-resolution image if thumbnail is being used
                            if (isThumbnail) {
                                tooltipImage.classList.add('thumbnail-image');
                                tooltipImage.style.cursor = 'zoom-in';
                                tooltipImage.title = 'Click to view full resolution';
                                // Ensure image is clickable even if tooltip has pointer-events: none
                                tooltipImage.style.pointerEvents = 'auto';

                                // Remove any existing click handlers
                                const newHandler = async (e) => {
                                    e.stopPropagation();
                                    e.preventDefault();
                                    // Prevent multiple clicks while loading
                                    if (tooltipImage.dataset.loading === 'true') {
                                        return;
                                    }

                                    // Get the current item name from the tooltip to ensure we're loading the right image
                                    const currentItemName = this.tooltip.querySelector('.tooltip-title')?.textContent;
                                    if (!currentItemName || currentItemName !== item.name) {
                                        // Tooltip has changed, don't load image
                                        return;
                                    }

                                    // Get the current image path dynamically (don't use closure variable)
                                    let currentImagePath = this.getImagePath(item.name);
                                    // Remove extension if present (getFullImagePath expects path without extension)
                                    if (currentImagePath && !currentImagePath.startsWith('data:image')) {
                                        currentImagePath = currentImagePath.replace(/\.(jpg|jpeg|png)$/i, '');
                                    }

                                    // Open modal with full-resolution image
                                    this.openImageModal(currentImagePath, item.name);
                                };

                                // Add click handler to load full-resolution image
                                tooltipImage.addEventListener('click', newHandler);
                            } else {
                                tooltipImage.classList.remove('thumbnail-image');
                                tooltipImage.style.cursor = '';
                                tooltipImage.title = '';
                                tooltipImage.style.pointerEvents = '';
                            }

                            // Reposition tooltip now that image is loaded and height has changed
                            if (!isTouchPrimary) {
                                positionTooltip();
                            }
                        }
                    };
                    img.onerror = () => {
                        // Image failed to load, keep it hidden
                        this.recordImageFailure(imageSrc);
                        tooltipImage.style.display = 'none';
                    };
                    // Start loading the image
                    img.src = imageSrc;
                } else {
                    // Image doesn't exist, keep it hidden
                    tooltipImage.style.display = 'none';
                }
            });
        } else {
            // No image path, keep it hidden
            tooltipImage.style.display = 'none';
        }

        this.tooltip.classList.add('visible');
    }

    hideTooltip() {
        this.cancelTooltipHide();
        this.hideUnitConversions();
        this.tooltipItem = null;
        this.experiences?.audio.stop();
        this.tooltip.classList.remove('visible');
        // Reset mobile-specific class
        this.tooltip.classList.remove('mobile-pinned');
        // Clear pinned state
        this.tooltipPinned = false;
        // Reset z-index to default
        this.tooltip.style.zIndex = '';
        // Reset pointer-events to none so tooltip doesn't block interactions when hidden
        this.tooltip.style.pointerEvents = 'none';
        // Clear any image src to prevent invisible overlays
        const tooltipImage = this.tooltip.querySelector('.tooltip-image');
        if (tooltipImage) {
            tooltipImage.src = '';
            tooltipImage.style.display = 'none';
            tooltipImage.style.pointerEvents = '';
        }
    }

    getImagePath(itemName) {
        // First check if there's a custom item with imageData
        if (this.editor) {
            const allItems = this.editor.getAllItemsForEditor();
            const item = allItems.find(i => i.name === itemName);

            // Check if imageData is explicitly null (image was removed)
            if (item && item.imageData === null) {
                return null;
            }

            if (item && item.imageData) {
                // Return the data URL directly
                return item.imageData;
            }
        }

        // Otherwise use the original logic
        const sanitizedDimension = this.currentDimension
            .replace(/[^\w\s-]/g, '')  // Remove special characters
            .replace(/[-\s]+/g, '_')    // Replace spaces and dashes with underscores
            .toLowerCase();

        const sanitizedName = itemName
            .replace(/[^\w\s-]/g, '')  // Remove special characters
            .replace(/[-\s]+/g, '_')    // Replace spaces and dashes with underscores
            .toLowerCase();

        const baseFilename = `${sanitizedDimension}_${sanitizedName}`;
        return `images/${baseFilename}`;
    }

    async checkImageExists(imagePath, useThumbnail = true) {
        // Check if it's a data URL (custom uploaded image)
        if (imagePath.startsWith('data:image')) {
            return imagePath;
        }

        const cacheKey = `exists_${imagePath}_${useThumbnail}`;
        if (this.imageExistenceCache.has(cacheKey)) {
            return this.imageExistenceCache.get(cacheKey);
        }

        try {
            // Normalize the path - remove extension if present, we'll add it back
            let basePath = imagePath;
            const hasExtension = /\.(jpg|jpeg|png)$/i.test(imagePath);
            if (hasExtension) {
                basePath = imagePath.replace(/\.(jpg|jpeg|png)$/i, '');
            }

            // First try thumbnail if requested (for initial display)
            if (useThumbnail) {
                const thumbPath = basePath.replace('images/', 'images/thumbs/');
                try {
                    const thumbJpgResponse = await fetch(`${thumbPath}.jpg`, { method: 'HEAD' });
                    if (thumbJpgResponse.ok) {
                        const result = { path: `${thumbPath}.jpg`, isThumbnail: true, fullPath: basePath };
                        this.imageExistenceCache.set(cacheKey, result);
                        return result;
                    }
                } catch (e) { /* ignore and continue */ }
            }

            // Try full-resolution JPG
            try {
                const jpgResponse = await fetch(`${basePath}.jpg`, { method: 'HEAD' });
                if (jpgResponse.ok) {
                    const result = useThumbnail ? { path: `${basePath}.jpg`, isThumbnail: false, fullPath: `${basePath}.jpg` } : `${basePath}.jpg`;
                    this.imageExistenceCache.set(cacheKey, result);
                    return result;
                }
            } catch (e) { /* ignore and continue */ }

            // Try full-resolution PNG if JPG doesn't exist
            try {
                const pngResponse = await fetch(`${basePath}.png`, { method: 'HEAD' });
                if (pngResponse.ok) {
                    const result = useThumbnail ? { path: `${basePath}.png`, isThumbnail: false, fullPath: `${basePath}.png` } : `${basePath}.png`;
                    this.imageExistenceCache.set(cacheKey, result);
                    return result;
                }
            } catch (e) { /* ignore and continue */ }

            this.imageExistenceCache.set(cacheKey, null);
            return null; // Neither exists
        } catch (error) {
            this.imageExistenceCache.set(cacheKey, null);
            return null;
        }
    }

    async getFullImagePath(imagePath) {
        // Get full-resolution image path (for click-to-view-full)
        if (imagePath.startsWith('data:image')) {
            return imagePath;
        }

        const cacheKey = `full_${imagePath}`;
        if (this.imageExistenceCache.has(cacheKey)) {
            return this.imageExistenceCache.get(cacheKey);
        }

        try {
            // Try JPG first
            try {
                const jpgResponse = await fetch(`${imagePath}.jpg`, { method: 'HEAD' });
                if (jpgResponse.ok) {
                    const result = `${imagePath}.jpg`;
                    this.imageExistenceCache.set(cacheKey, result);
                    return result;
                }
            } catch (e) { /* ignore */ }

            // Try PNG if JPG doesn't exist
            try {
                const pngResponse = await fetch(`${imagePath}.png`, { method: 'HEAD' });
                if (pngResponse.ok) {
                    const result = `${imagePath}.png`;
                    this.imageExistenceCache.set(cacheKey, result);
                    return result;
                }
            } catch (e) { /* ignore */ }

            this.imageExistenceCache.set(cacheKey, null);
            return null;
        } catch (error) {
            this.imageExistenceCache.set(cacheKey, null);
            return null;
        }
    }

    convertValue(value) {
        if (!this.currentUnit) return value;

        const unit = this.getCurrentUnitDefinition();
        if (!unit) return value;

        if (this.isSoundIntensityDecibelUnit(unit)) {
            if (value <= 0) return Number.NEGATIVE_INFINITY;
            return 10 * Math.log10(value / 1e-12);
        }

        // For costs, handle currency conversion
        if (this.currentDimension === 'costs' && unit.name !== 'USD') {
            // This would use exchange rates - simplified for now
            return value * unit.conversion_factor;
        }

        const convertedValue = value * unit.conversion_factor;

        // Debug: Log conversion for specific items
        if (value < CONFIG.DEBUG_SMALL_VALUE_THRESHOLD) { // Very small values that might be atomic/molecular forces
            console.log('Converting small value:', {
                originalValue: value,
                convertedValue: convertedValue,
                conversionFactor: unit.conversion_factor,
                unit: unit.name
            });
        }

        return convertedValue;
    }

    convertValueForPlot(value) {
        if (this.isSoundIntensityDecibelUnit()) {
            return value;
        }
        return this.convertValue(value);
    }

    formatValueForCurrentUnit(value, precision = 0, forTooltip = false) {
        const convertedValue = this.convertValue(value);
        if (this.isSoundIntensityDecibelUnit()) {
            return this.formatter.formatLinearNumber(convertedValue, Math.max(precision, forTooltip ? 1 : 0));
        }
        return this.formatNumber(convertedValue, precision, forTooltip);
    }

    formatAxisValue(value, precision = 0) {
        if (this.isSoundIntensityDecibelUnit()) {
            const convertedValue = value > 0 ? 10 * Math.log10(value / 1e-12) : Number.NEGATIVE_INFINITY;
            return this.formatter.formatLinearNumber(convertedValue, precision);
        }
        return this.formatNumber(value, precision);
    }

    async loadExchangeRates() {
        try {
            const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
            this.exchangeRates = await response.json();
        } catch (error) {
            console.warn('Failed to load exchange rates:', error);
        }
    }

    resizePlot() {
        if (this.experiences?.active) { this.experiences.refresh(); return; }
        // Preserve current zoom state before resizing
        const currentDomain = this.xScale.domain();
        const wasZoomed = this.originalXDomain && this.isDomainZoomed(currentDomain, this.originalXDomain);

        this.plot.updateDimensions();

        // SVG width is now updated in updateDimensions() to match container exactly

        // Update xScale range with new width (domain stays the same - preserves data view)
        this.xScale.range([0, this.width]);

        // Update zoom behavior translate extent for new width
        if (this.zoomBehavior) {
            this.zoomBehavior.translateExtent(this.getZoomTranslateExtent());
        }

        // Recalculate transform to match current domain with new width
        // This prevents teleportation when panning after resize
        if (wasZoomed && this.zoomBehavior) {
            const newTransform = this.calculateTransformFromDomain(currentDomain);
            if (!this.isUpdatingTransform) {
                this.isUpdatingTransform = true;
                this.mainGroup.call(this.zoomBehavior.transform, newTransform);
                this.isUpdatingTransform = false;
            }
        }

        // Only update plot if not zoomed, or update while preserving zoom state
        if (wasZoomed) {
            // Preserve current zoom level and vertical layout; just adapt to new size
            if (this.dimensionData && this.yScale && this.originalItemsHeight !== null) {
                // Use the stored original itemsHeight to preserve exact vertical layout
                // This prevents items from shifting when mobile config changes FIXED_VERTICAL_SPACING
                const itemsHeight = this.originalItemsHeight;

                // Recompute SVG height from original vertical extent (don't change layout)
                const requiredSvgHeight = itemsHeight + this.margin.top + this.margin.bottom;
                const svgHeight = Math.max(CONFIG.MIN_SVG_HEIGHT, requiredSvgHeight);

                // Update SVG height
                this.svg.attr('height', svgHeight);

                // Update inner plot height
                this.height = svgHeight - this.margin.top - this.margin.bottom;

                // Update yScale range to use the new height, keeping the same domain
                this.yScale.range([this.height, 0]);
                // Ensure domain matches original itemsHeight exactly
                this.yScale.domain([0, itemsHeight]);

                // Update zoom background rectangle to cover full container
                if (this.zoomBackground) {
                    const svgWidth = +this.svg.attr('width') || 0;
                    this.zoomBackground
                        .attr('width', svgWidth)
                        .attr('height', this.height + this.margin.top + this.margin.bottom);
                }

                // Update axes positions based on yScale
                this.xAxis.attr('transform', `translate(0,${this.yScale(0)})`);
                this.xAxisTop.attr('transform', `translate(0,${this.yScale(itemsHeight)})`);
            }

            // Now update the visual elements with correct heights
            this.plot.updatePlotAfterZoom();
        } else {
            this.plot.updatePlot();

            // Update sticky top axis after resize
            if (this.updateStickyAxis) {
                this.updateStickyAxis();
            }

        }
    }

    getAllItems() {
        const allItems = [];
        const customItems = this.customItems[this.currentDimension] || [];

        // Get original items with potential overrides or deletions
        if (this.dimensionData.items) {
            this.dimensionData.items.forEach((item, index) => {
                // Check if this item is marked as deleted
                const isDeleted = customItems.some(
                    custom => custom.originalIndex === index && custom.isDeleted
                );

                if (isDeleted) {
                    // Skip deleted items
                    return;
                }

                // Check if there's an override for this item
                const override = customItems.find(
                    custom => custom.originalIndex === index && custom.isOverride && !custom.isDeleted
                );

                if (override) {
                    // Merge override with original - ensure all fields are included
                    const mergedItem = {
                        ...item,
                        name: override.name !== undefined ? override.name : item.name,
                        value: override.value !== undefined ? override.value : item.value,
                        description: override.description !== undefined ? override.description : item.description,
                        source: override.source !== undefined ? override.source : item.source,
                        imageData: override.imageData !== undefined ? override.imageData : undefined
                    };
                    allItems.push({
                        ...mergedItem,
                        convertedValue: this.convertValueForPlot(mergedItem.value)
                    });
                } else {
                    allItems.push({
                        ...item,
                        convertedValue: this.convertValueForPlot(item.value)
                    });
                }
            });
        }

        // Add custom items (not overrides, not deleted)
        customItems.forEach(customItem => {
            if (customItem.isCustom && !customItem.isOverride && !customItem.isDeleted) {
                // Validate item before adding - must have name and valid value
                const value = parseFloat(customItem.value);
                const hasValidName = customItem.name && customItem.name.trim().length > 0;
                const hasValidValue = !isNaN(value) && isFinite(value) && value !== 0;

                if (hasValidName && hasValidValue) {
                    allItems.push({
                        ...customItem,
                        convertedValue: this.convertValueForPlot(customItem.value)
                    });
                }
            }
        });

        // Filter out any items with invalid names or values
        return ScaleMath.displayItems(allItems.filter(item => {
            const value = parseFloat(item.value);
            const hasValidName = item.name && item.name.trim().length > 0;
            const hasValidValue = !isNaN(value) && isFinite(value) && value !== 0;
            return hasValidName && hasValidValue;
        }));
    }

    updateUnitDescription() {
        if (!this.currentUnit || !this.dimensionData) {
            this.unitDescription.textContent = '';
            this.unitDescription.style.display = 'none'; // Hide when empty
            return;
        }

        const unit = this.dimensionData.units.find(u => u.name === this.currentUnit);
        if (!unit) {
            this.unitDescription.textContent = '';
            this.unitDescription.style.display = 'none';
            return;
        }

        // Check for unit description override
        const unitIndex = this.dimensionData.units.indexOf(unit);
        const unitDescOverride = this.editor?.unitOverrides[this.currentDimension]?.[unitIndex]?.description;
        const unitDesc = unitDescOverride !== undefined
            ? unitDescOverride
            : (unit.description || '');

        if (unitDesc) {
            this.setRichText(this.unitDescription, unitDesc);
            this.unitDescription.style.display = '';
        } else {
            this.unitDescription.textContent = '';
            this.unitDescription.style.display = 'none'; // Hide when empty
        }
    }

    setRichText(element, text) {
        if (!element) return;
        element.innerHTML = this.renderMarkdown(text);
        window.requestAnimationFrame(() => {
            this.typesetMath(element, text);
        });
    }

    buildTooltipDescriptionMarkdown(item, baseText) {
        const sections = [];
        if (baseText) {
            sections.push(this.stripSelfSourceLinks(baseText, item?.source));
        }

        const trace = item?.facts?.source_trace || null;
        const calculationBits = [];
        if (trace?.source_value_text) {
            calculationBits.push(`Source figure: ${this.formatTraceSourceValue(trace.source_value_text, trace.source_unit)}`);
        }
        if (trace?.derivation_note) {
            calculationBits.push(this.formatTraceDerivation(trace.derivation_note));
            calculationBits.push(...this.buildDerivedEstimateDetails(item, trace));
        }
        if (trace?.conversion_note) {
            calculationBits.push(this.formatTracePlainText(trace.conversion_note));
        }
        if (trace?.source_basis) {
            calculationBits.push(`Basis: ${this.formatTracePlainText(trace.source_basis)}`);
        }
        if (item?.qualifiers?.assumption) {
            calculationBits.push(`Assumptions: ${this.formatTracePlainText(item.qualifiers.assumption)}`);
        }

        if (calculationBits.length > 0) {
            sections.push(`### How It Was Estimated\n${calculationBits.join('\n\n')}`);
        }

        return sections.join('\n\n').trim();
    }

    sanitizeTraceText(value) {
        if (value === null || value === undefined) return '';
        return String(value)
            .replace(/\u0007/g, '\\approx ')
            .replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    normalizeUrlForComparison(value) {
        if (!value) return '';
        try {
            const url = new URL(String(value), window.location.href);
            const pathname = url.pathname.replace(/\/+$/, '');
            return `${url.origin}${pathname}${url.search}`;
        } catch (_error) {
            return String(value).trim().replace(/\/+$/, '');
        }
    }

    stripSelfSourceLinks(markdown, sourceUrl) {
        if (!markdown || !sourceUrl) {
            return markdown || '';
        }

        const normalizedSource = this.normalizeUrlForComparison(sourceUrl);
        return String(markdown).replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, label, href) => {
            return this.normalizeUrlForComparison(href) === normalizedSource ? label : match;
        });
    }

    escapeHtml(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    formatUnitSymbolHTML(symbol) {
        if (!symbol) return '';
        let html = this.escapeHtml(symbol);
        // Support both compact forms (m^2, l_P) and braced forms (m^{2}, l_{P}).
        html = html.replace(/\^\{([^}]+)\}/g, '<sup>$1</sup>');
        html = html.replace(/_\{([^}]+)\}/g, '<sub>$1</sub>');
        html = html.replace(/\^([A-Za-z0-9+\-]+)/g, '<sup>$1</sup>');
        html = html.replace(/_([A-Za-z0-9+\-]+)/g, '<sub>$1</sub>');
        return html;
    }

    formatUnitSymbolDisplayText(symbol) {
        if (!symbol) return '';
        let text = String(symbol);
        text = text.replace(/\^\{([^}]+)\}/g, (_, value) => this.toSuperscript(value));
        text = text.replace(/_\{([^}]+)\}/g, (_, value) => this.formatSubscriptTokenForSelect(value));
        text = text.replace(/\^([A-Za-z0-9+\-]+)/g, (_, value) => this.toSuperscript(value));
        text = text.replace(/_([A-Za-z0-9+\-]+)/g, (_, value) => this.formatSubscriptTokenForSelect(value));
        return text;
    }

    unitSymbolToLatex(symbol) {
        if (!symbol) return '';
        let latex = String(symbol).trim();
        if (/\\[A-Za-z]/.test(latex)) {
            return latex;
        }
        latex = latex.replace(/µ|μ/g, '\\mu ');
        latex = latex.replace(/\^\{([^}]+)\}/g, '^{$1}');
        latex = latex.replace(/_\{([^}]+)\}/g, '_{$1}');
        latex = latex.replace(/\^([A-Za-z0-9+\-]+)/g, '^{$1}');
        latex = latex.replace(/_([A-Za-z0-9+\-]+)/g, '_{$1}');
        return this.romanizeUnitLatex(latex);
    }

    romanizeUnitLatex(latex) {
        if (!latex) return '';
        return String(latex).replace(/\\[A-Za-z]+|[A-Za-z]+/g, (token) => {
            if (token.startsWith('\\')) return token;
            return `\\mathrm{${token}}`;
        });
    }

    formatSubscriptTokenForSelect(value) {
        const token = String(value || '');
        // Native <select><option> cannot render true math HTML.
        // Only use unicode subscripts when the full token is representable cleanly.
        // For symbolic word-like subscripts (earth, sun, jup), preserve underscore text.
        if (/^[0-9+\-]+$/.test(token)) {
            return this.toSubscript(token);
        }
        return `_${token}`;
    }

    formatTooltipValueHTML(formattedValue, unitSymbol) {
        const valueHtml = (!this.usesLinearDisplayValues() && this.notationMode === 'mathematical')
            ? formattedValue
            : this.escapeHtml(formattedValue);
        const unitHtml = this.formatUnitSymbolHTML(unitSymbol);
        return unitHtml ? `${valueHtml} ${unitHtml}` : valueHtml;
    }

    toSuperscript(value) {
        const superscripts = {
            '0': '⁰',
            '1': '¹',
            '2': '²',
            '3': '³',
            '4': '⁴',
            '5': '⁵',
            '6': '⁶',
            '7': '⁷',
            '8': '⁸',
            '9': '⁹',
            '+': '⁺',
            '-': '⁻',
        };
        return String(value)
            .split('')
            .map(char => superscripts[char] || char)
            .join('');
    }

    toSubscript(value) {
        const subscripts = {
            '0': '₀',
            '1': '₁',
            '2': '₂',
            '3': '₃',
            '4': '₄',
            '5': '₅',
            '6': '₆',
            '7': '₇',
            '8': '₈',
            '9': '₉',
            '+': '₊',
            '-': '₋',
            'a': 'ₐ',
            'e': 'ₑ',
            'h': 'ₕ',
            'i': 'ᵢ',
            'j': 'ⱼ',
            'k': 'ₖ',
            'l': 'ₗ',
            'm': 'ₘ',
            'n': 'ₙ',
            'o': 'ₒ',
            'p': 'ₚ',
            'r': 'ᵣ',
            's': 'ₛ',
            't': 'ₜ',
            'u': 'ᵤ',
            'v': 'ᵥ',
            'x': 'ₓ',
            'A': 'ₐ',
            'E': 'ₑ',
            'H': 'ₕ',
            'I': 'ᵢ',
            'J': 'ⱼ',
            'K': 'ₖ',
            'L': 'ₗ',
            'M': 'ₘ',
            'N': 'ₙ',
            'O': 'ₒ',
            'P': 'ₚ',
            'R': 'ᵣ',
            'S': 'ₛ',
            'T': 'ₜ',
            'U': 'ᵤ',
            'V': 'ᵥ',
            'X': 'ₓ',
        };
        return String(value)
            .split('')
            .map(char => subscripts[char] || char)
            .join('');
    }

    normalizeUnitSignature(text) {
        return this.sanitizeTraceText(text)
            .toLowerCase()
            .replace(/\s+/g, '')
            .replace(/[(){}\[\],.~≈]/g, '');
    }

    isNumericLikeSourceValue(text) {
        const value = this.sanitizeTraceText(text);
        return /^[<>~≈]?\s*[+-]?(?:\d+(?:,\d{3})*|\d*\.\d+)(?:e[+-]?\d+)?(?:\s*[%°])?$/.test(value);
    }

    shouldAppendSourceUnit(valueText, unitText) {
        const value = this.sanitizeTraceText(valueText);
        const unit = this.sanitizeTraceText(unitText);
        if (!value || !unit || !this.isNumericLikeSourceValue(value)) {
            return false;
        }
        return !this.normalizeUnitSignature(value).includes(this.normalizeUnitSignature(unit));
    }

    formatTracePlainText(text) {
        let value = this.sanitizeTraceText(text);
        if (!value) return '';
        value = value.replace(/\\approx\b/g, '≈');
        value = value.replace(/\\times\b/g, '×');
        value = value.replace(/\s+[x*]\s+/g, ' × ');
        value = value.replace(/(\d+(?:\.\d+)?)\^([+-]?\d+)/g, (_, base, exponent) => `${base}${this.toSuperscript(exponent)}`);
        value = value.replace(/([A-Za-z]+)\^([+-]?\d+)/g, (_, base, exponent) => `${base}${this.toSuperscript(exponent)}`);
        value = value.replace(/([+-]?\d+(?:\.\d+)?)e([+-]?\d+)/gi, (_, mantissa, exponent) => {
            return `${mantissa} × 10${this.toSuperscript(exponent)}`;
        });
        return value;
    }

    looksLikeLatexExpression(text) {
        const value = this.sanitizeTraceText(text);
        return /\\[A-Za-z]+|[_^{}]/.test(value);
    }

    normalizeLatexExpression(text) {
        let value = this.sanitizeTraceText(text);
        if (!value) return '';
        const compact = value.toLowerCase().replace(/\s+/g, '').replace(/\\/g, '');
        if (compact === 'pi*r^2' || compact === 'pir^2') {
            return '\\pi r^2';
        }
        if (compact === '4*pi*r^2' || compact === '4pir^2') {
            return '4\\pi r^2';
        }
        value = value.replace(/\\u0007/g, '\\approx ');
        value = value.replace(/\b4\s*\*\s*pi\s*\*\s*r\^2\b/gi, '4 \\pi r^2');
        value = value.replace(/\b4\s*pi\s*r\^2\b/gi, '4 \\pi r^2');
        value = value.replace(/\bpi\s*\*\s*r\^2\b/gi, '\\pi r^2');
        value = value.replace(/\bpi\s*r\^2\b/gi, '\\pi r^2');
        value = value.replace(/(^|[^\\])pi\b/g, '$1\\pi');
        value = value.replace(/\^(\{[^}]+\}|[A-Za-z0-9+\-.]+)/g, (_match, exponentToken) => {
            if (exponentToken.startsWith('{')) return `^${exponentToken}`;
            return `^{${exponentToken}}`;
        });
        value = value.replace(/_(\{[^}]+\}|[A-Za-z0-9+\-.]+)/g, (_match, subToken) => {
            if (subToken.startsWith('{')) return `_${subToken}`;
            return `_{${subToken}}`;
        });
        value = value.replace(/(^|[^\\])count\b/gi, '$1\\mathrm{count}');
        value = value.replace(/\s+[x*]\s+/g, ' \\times ');
        value = value.replace(/([+-]?\d+(?:\.\d+)?)e([+-]?\d+)/gi, '$1 \\\\times 10^{$2}');
        return value;
    }

    formatTraceSourceValue(sourceValueText, sourceUnit) {
        const value = this.sanitizeTraceText(sourceValueText);
        const unit = this.sanitizeTraceText(sourceUnit);
        const combined = this.shouldAppendSourceUnit(value, unit) ? `${value} ${unit}` : value;
        return this.formatTracePlainText(combined);
    }

    formatTraceDerivation(text) {
        const compact = this.sanitizeTraceText(text).toLowerCase().replace(/\s+/g, '').replace(/\\/g, '');
        if (compact === 'pi*r^2' || compact === 'pir^2') {
            return '$$\\pi r^2$$';
        }
        if (compact === '4*pi*r^2' || compact === '4pir^2') {
            return '$$4\\pi r^2$$';
        }
        if (this.looksLikeLatexExpression(text)) {
            return `$$${this.normalizeLatexExpression(text)}$$`;
        }
        return `Formula: ${this.formatTracePlainText(text)}`;
    }

    buildDerivedEstimateDetails(item, trace) {
        if (this.currentDimension !== 'area') {
            return [];
        }

        const formula = this.sanitizeTraceText(trace?.derivation_note);
        const area = Number(item?.value);
        if (!formula || !Number.isFinite(area) || area <= 0) {
            return [];
        }

        let radius = null;
        let prefix = 'Using';
        const normalized = formula.toLowerCase();

        if (/4\s*(?:\\times\s*)?\\?pi\s*r\^?2|4\s*\*\s*pi\s*\*\s*r\^?2/.test(normalized)) {
            radius = Math.sqrt(area / (4 * Math.PI));
            prefix = 'Treating the object as a sphere with';
        } else if (/(?:^|[^a-z])\\?pi\s*r\^?2|pi\s*\*\s*r\^?2/.test(normalized)) {
            radius = Math.sqrt(area / Math.PI);
        }

        if (!radius || !Number.isFinite(radius) || radius <= 0) {
            return [];
        }

        return [`${prefix} $r \\approx ${this.formatLengthLatex(radius)}$.`];
    }

    formatLengthLatex(meters) {
        const absolute = Math.abs(Number(meters));
        if (!Number.isFinite(absolute) || absolute === 0) {
            return '0\\,\\mathrm{m}';
        }

        const units = [
            { min: 3.085677581e25, factor: 3.085677581e25, latex: '\\mathrm{Gpc}' },
            { min: 9.460730472e24, factor: 9.460730472e24, latex: '\\mathrm{Gly}' },
            { min: 3.085677581e22, factor: 3.085677581e22, latex: '\\mathrm{Mpc}' },
            { min: 9.460730472e18, factor: 9.460730472e18, latex: '\\mathrm{ly}' },
            { min: 1e12, factor: 1e12, latex: '\\mathrm{Tm}' },
            { min: 1e9, factor: 1e9, latex: '\\mathrm{Gm}' },
            { min: 1e6, factor: 1e6, latex: '\\mathrm{Mm}' },
            { min: 1e3, factor: 1e3, latex: '\\mathrm{km}' },
            { min: 1, factor: 1, latex: '\\mathrm{m}' },
            { min: 1e-2, factor: 1e-2, latex: '\\mathrm{cm}' },
            { min: 1e-3, factor: 1e-3, latex: '\\mathrm{mm}' },
            { min: 1e-6, factor: 1e-6, latex: '\\mu\\mathrm{m}' },
            { min: 1e-9, factor: 1e-9, latex: '\\mathrm{nm}' },
            { min: 1e-12, factor: 1e-12, latex: '\\mathrm{pm}' },
            { min: 1e-15, factor: 1e-15, latex: '\\mathrm{fm}' },
        ];

        for (const unit of units) {
            if (absolute >= unit.min) {
                const scaled = meters / unit.factor;
                if (Math.abs(scaled) >= 1e4) {
                    continue;
                }
                return `${this.formatLatexNumber(scaled)}\\,${unit.latex}`;
            }
        }

        return `${this.formatLatexNumberScientific(meters)}\\,\\mathrm{m}`;
    }

    formatLatexNumber(value) {
        const absolute = Math.abs(value);
        let digits = 2;
        if (absolute >= 100) {
            digits = 0;
        } else if (absolute >= 10) {
            digits = 1;
        }
        return Number(value).toFixed(digits).replace(/\.0+$/, '').replace(/(\.\d*?)0+$/, '$1');
    }

    formatLatexNumberScientific(value) {
        const exponent = Math.floor(Math.log10(Math.abs(value)));
        const mantissa = value / (10 ** exponent);
        return `${this.formatLatexNumber(mantissa)} \\times 10^{${exponent}}`;
    }

    latexifyInlineMath(text) {
        if (!text) return '';
        return String(text)
            .replace(/×/g, ' \\\\times ')
            .replace(/\*/g, ' \\\\times ')
            .replace(/\bpi\b/g, '\\\\pi')
            .replace(/([+-]?\\d+(?:\\.\\d+)?)e([+-]?\\d+)/gi, '$1 \\\\times 10^{$2}');
    }

    containsMath(text) {
        if (!text) return false;
        return /\$\$[\s\S]+?\$\$|\$[^$\n]+\$|\\\([\s\S]+?\\\)|\\\[[\s\S]+?\\\]/.test(text);
    }

    typesetMath(element, text, attempt = 0) {
        if (!this.containsMath(text)) return;
        if (window.MathJax && typeof window.MathJax.typesetPromise === 'function') {
            const runTypeset = () => {
                if (typeof window.MathJax.typesetClear === 'function') {
                    window.MathJax.typesetClear([element]);
                }
                window.MathJax.typesetPromise([element]).catch(() => {
                    // Keep the rendered markdown even if math typesetting fails.
                });
            };

            if (window.MathJax.startup?.promise && typeof window.MathJax.startup.promise.then === 'function') {
                window.MathJax.startup.promise.then(runTypeset).catch(runTypeset);
            } else {
                runTypeset();
            }
            return;
        }

        if (attempt < 8) {
            window.setTimeout(() => this.typesetMath(element, text, attempt + 1), 150);
        }
    }

    typesetMathIfReady(element) {
        if (!element) return;
        const mathSource = element.textContent || element.innerHTML || '';
        this.typesetMath(element, mathSource);
    }

    preserveMathBlocks(text) {
        const mathBlocks = [];
        const placeholderText = String(text).replace(
            /\$\$[\s\S]+?\$\$|\$[^$\n]+\$|\\\([\s\S]+?\\\)|\\\[[\s\S]+?\\\]/g,
            (match) => {
                const placeholder = `@@MATH_BLOCK_${mathBlocks.length}@@`;
                mathBlocks.push(match);
                return placeholder;
            }
        );
        return { placeholderText, mathBlocks };
    }

    restoreMathBlocks(text, mathBlocks) {
        return mathBlocks.reduce(
            (restored, block, index) => restored.replaceAll(`@@MATH_BLOCK_${index}@@`, block),
            text
        );
    }

    /**
     * Render markdown-style text to HTML.
     */
    renderMarkdown(text) {
        if (!text) return '';
        const { placeholderText, mathBlocks } = this.preserveMathBlocks(text);

        if (window.marked) {
            const rawHtml = window.marked.parse(placeholderText, {
                breaks: true,
                gfm: true
            });
            if (window.DOMPurify) {
                return this.restoreMathBlocks(window.DOMPurify.sanitize(rawHtml), mathBlocks);
            }
            return this.restoreMathBlocks(rawHtml, mathBlocks);
        }

        let html = placeholderText
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
        html = html.replace(/\n{2,}/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');
        return this.restoreMathBlocks(`<p>${html}</p>`, mathBlocks);
    }

    async openImageModal(imagePath, itemName) {
        if (!this.imageModal || !this.imageModalImg) return;

        // Show loading state
        this.imageModalImg.src = '';
        this.imageModalImg.alt = itemName || 'Image';
        this.imageModal.classList.add('active');
        this.imageModalImg.style.opacity = '0.5';

        // Get full-resolution image path
        const fullPath = /\.(?:jpe?g|png|webp|svg)(?:\?|$)/i.test(imagePath)
            ? imagePath : await this.getFullImagePath(imagePath);
        if (fullPath) {
            const img = new Image();
            img.onload = () => {
                this.imageModalImg.src = fullPath;
                this.imageModalImg.alt = itemName || 'Image';
                this.imageModalImg.style.opacity = '1';
            };
            img.onerror = () => {
                this.closeImageModal();
            };
            img.src = fullPath;
        } else {
            this.closeImageModal();
        }
    }

    closeImageModal() {
        if (this.imageModal) {
            this.imageModal.classList.remove('active');
            if (this.imageModalImg) {
                this.imageModalImg.src = '';
            }
        }
    }

    showError(message) {
        // Simple error display - could be enhanced
        console.error(message);
        alert(message);
    }

    isMobileDevice() {
        // Detect if we're on a mobile/touch device
        return ('ontouchstart' in window) || window.matchMedia('(hover: none)').matches;
    }

    setupZoom() {
        // Store actual item extent (without the 0.1 multiplier) for zoom limits
        this.actualItemExtent = null;

        // Detect if we're on mobile to disable pinch zoom
        const isMobile = this.isMobileDevice();

        // Create a background rectangle for visual feedback and event capture
        // This covers the entire container (including margins) for seamless panning
        // Positioned relative to mainGroup (which is translated by margins)
        const svgWidth = +this.svg.attr('width') || 0;
        this.zoomBackground = this.mainGroup.insert('rect', ':first-child')
            .attr('class', 'zoom-background')
            .attr('x', -this.margin.left)
            .attr('y', -this.margin.top)
            .attr('width', svgWidth)
            .attr('height', this.height + this.margin.top + this.margin.bottom)
            .attr('fill', 'transparent')
            .attr('cursor', 'grab')
            .style('pointer-events', 'all')
            .style('touch-action', isMobile ? 'pan-y' : 'pan-y pinch-zoom');

        // Create zoom behavior that only affects x-axis
        this.zoomBehavior = d3.zoom()
            .scaleExtent([CONFIG.ZOOM_SCALE_MIN, CONFIG.ZOOM_SCALE_MAX]) // Will be constrained further in handleZoom
            .translateExtent(this.getZoomTranslateExtent()) // Allow panning horizontally with padding
            .filter((event) => {
                // On mobile, block wheel events and multi-touch gestures (pinch zoom)
                if (isMobile && (event.type === 'touchstart' || isTouchPointer)) {
                    return false;
                }

                // For mouse events, only allow on background (not on items)
                if (event.type === 'mousedown') {
                    const target = event.target;
                    // Check if clicking on an interactive element
                    if (target.classList && (
                        target.classList.contains('plot-item') ||
                        target.classList.contains('label-hover-area') ||
                        target.classList.contains('tap-target') ||
                        target.classList.contains('item-label')
                    )) {
                        return false;
                    }
                    // Check parent elements
                    let current = target;
                    for (let i = 0; i < CONFIG.PARENT_CHECK_DEPTH && current; i++) {
                        if (current.classList && (
                            current.classList.contains('item-group') ||
                            current.classList.contains('label-group')
                        )) {
                            return false;
                        }
                        current = current.parentNode;
                    }
                }

                return true;
            })
            .on('start', (event) => {
                // Change cursor when dragging starts
                if (this.zoomBackground) {
                    this.zoomBackground.attr('cursor', 'grabbing');
                }
                // Track initial drag position for vertical scrolling
                const startPosition = this.getSourceEventPosition(event.sourceEvent);
                if (startPosition) {
                    this.dragStartY = startPosition.y;
                    this.dragStartX = startPosition.x;
                } else {
                    this.dragStartY = null;
                    this.dragStartX = null;
                }
                this.lastScrollDeltaY = null;
            })
            .on('zoom', (event) => {
                // Handle vertical scrolling independently from horizontal panning (desktop only)
                const sourceEvent = event.sourceEvent;
                const pointerType = sourceEvent && sourceEvent.pointerType ? sourceEvent.pointerType.toLowerCase() : '';
                const isTouchLike = (sourceEvent && sourceEvent.type && sourceEvent.type.startsWith('touch'))
                    || pointerType === 'touch'
                    || pointerType === 'pen';

                if (!isTouchLike) {
                    const currentPosition = this.getSourceEventPosition(sourceEvent);
                    if (this.dragStartY !== null && currentPosition) {
                        const deltaY = currentPosition.y - this.dragStartY;
                        if (Math.abs(deltaY) > CONFIG.VERTICAL_SCROLL_THRESHOLD) {
                            const scrollAmount = deltaY - (this.lastScrollDeltaY || 0);
                            window.scrollBy(0, -scrollAmount);
                            this.lastScrollDeltaY = deltaY;
                        }
                    }
                }

                // Always handle horizontal zoom/pan (works simultaneously with vertical scrolling)
                this.handleZoom(event);
            })
            .on('end', () => {
                // Change cursor back when dragging ends
                if (this.zoomBackground) {
                    this.zoomBackground.attr('cursor', 'grab');
                }
                // Reset drag tracking
                this.dragStartY = null;
                this.dragStartX = null;
                this.lastScrollDeltaY = null;
                this.touchStartOnItem = null;
                this.touchStartPosition = null;
            });

        // Apply zoom to the main group - it will receive events
        // Items on top will still receive their own pointer events
        this.mainGroup
            .call(this.zoomBehavior)
            .style('touch-action', isMobile ? 'pan-y' : 'pan-y pinch-zoom');

        // Add double-click to reset zoom (only on background)
        this.mainGroup.on('dblclick', (event) => {
            // Only reset if not clicking on an item
            const target = event.target;
            let isInteractive = false;

            if (target.classList && (
                target.classList.contains('plot-item') ||
                target.classList.contains('label-hover-area') ||
                target.classList.contains('tap-target')
            )) {
                isInteractive = true;
            }

            if (!isInteractive) {
                let current = target;
                for (let i = 0; i < CONFIG.PARENT_CHECK_DEPTH && current; i++) {
                    if (current.classList && (
                        current.classList.contains('item-group') ||
                        current.classList.contains('label-group')
                    )) {
                        isInteractive = true;
                        break;
                    }
                    current = current.parentNode;
                }
            }

            if (!isInteractive) {
                this.resetZoom();
            }
        });
    }

    setupZoomControls() {
        const controls = document.querySelector('.zoom-controls');
        const plotContainer = document.getElementById('plot-container');
        if (!controls || !plotContainer) return;

        // Ensure consistent grid layout even if CSS fails to load (Safari quirks)
        controls.style.display = 'grid';
        controls.style.gridTemplateColumns = 'repeat(3, 1fr)';
        controls.style.gridTemplateRows = 'repeat(2, 1fr)';
        controls.style.gridTemplateAreas = '"left right plus" "reset reset minus"';

        // Move controls to body so they can float independently of plot container
        if (controls.parentNode !== document.body) {
            document.body.appendChild(controls);
        }
        controls.classList.add('zoom-controls-floating');

        const buttons = controls.querySelectorAll('.zoom-btn');
        const areaMap = {
            'pan-left': 'left',
            'pan-right': 'right',
            'zoom-in': 'plus',
            'zoom-out': 'minus',
            'reset': 'reset'
        };

        buttons.forEach(button => {
            const action = button.getAttribute('data-action');
            if (!action) return;

            button.type = 'button';
            button.style.display = 'flex';
            button.style.alignItems = 'center';
            button.style.justifyContent = 'center';
            if (areaMap[action]) {
                button.style.gridArea = areaMap[action];
            }

            // Helper function to perform a single step of the action
            const performAction = (useTransition = false) => {
                if (!this.zoomBehavior || !this.mainGroup) return;

                const zoomCenter = [
                    (this.width || 0) / 2,
                    (this.height || 0) / 2
                ];

                switch (action) {
                    case 'zoom-in':
                        if (useTransition) {
                            this.mainGroup.transition()
                                .duration(200)
                                .call(this.zoomBehavior.scaleBy, 1.5, zoomCenter);
                        } else {
                            this.mainGroup
                                .call(this.zoomBehavior.scaleBy, 1.03, zoomCenter);
                        }
                        break;
                    case 'zoom-out':
                        if (useTransition) {
                            this.mainGroup.transition()
                                .duration(200)
                                .call(this.zoomBehavior.scaleBy, 1 / 1.5, zoomCenter);
                        } else {
                            this.mainGroup
                                .call(this.zoomBehavior.scaleBy, 1 / 1.03, zoomCenter);
                        }
                        break;
                    case 'pan-left':
                    case 'pan-right': {
                        // Get current zoom level to adjust pan distance
                        const currentTransform = d3.zoomTransform(this.mainGroup.node());
                        const zoomLevel = currentTransform ? currentTransform.k : 1;
                        // Pan distance is inversely proportional to zoom level (more zoomed in = smaller pan)
                        const basePanDistance = (this.width * 0.04) / zoomLevel;
                        const panDistance = action === 'pan-left' ? basePanDistance : -basePanDistance;
                        if (useTransition) {
                            this.mainGroup.transition()
                                .duration(200)
                                .call(this.zoomBehavior.translateBy, panDistance, 0);
                        } else {
                            this.mainGroup
                                .call(this.zoomBehavior.translateBy, panDistance, 0);
                        }
                        break;
                    }
                    case 'reset':
                        this.resetZoom();
                        break;
                    default:
                        break;
                }
            };

            // Stop continuous action
            const stopAction = () => {
                if (this.buttonIntervals[action]) {
                    clearInterval(this.buttonIntervals[action]);
                    delete this.buttonIntervals[action];
                }
            };

            // Start continuous action (for pan/zoom buttons only, not reset)
            const startAction = (event) => {
                event.preventDefault();
                if (action === 'reset') {
                    // Reset button works on click only
                    performAction(true);
                    return;
                }

                // Perform one smooth step immediately (no transition for responsiveness)
                performAction(false);

                // Then repeat with small, transition-free steps
                const intervalId = setInterval(() => {
                    performAction(false);
                }, 40); // Repeat every 40ms for smooth motion

                this.buttonIntervals[action] = intervalId;
            };

            // Handle mouse events
            button.addEventListener('mousedown', startAction);
            button.addEventListener('mouseup', stopAction);
            button.addEventListener('mouseleave', stopAction); // Stop if mouse leaves button

            // Handle touch events for mobile
            button.addEventListener('touchstart', (event) => {
                startAction(event);
                // Prevent click event from firing after touch
                event.preventDefault();
            });
            button.addEventListener('touchend', stopAction);
            button.addEventListener('touchcancel', stopAction);

            // Also keep click handler for reset button and as fallback
            if (action === 'reset') {
                button.addEventListener('click', (event) => {
                    event.preventDefault();
                    performAction(true);
                });
            }
        });

        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        controls.classList.add('is-visible');
                    } else {
                        controls.classList.remove('is-visible');
                    }
                });
            }, { root: null, threshold: 0.1 });
            observer.observe(plotContainer);
        } else {
            controls.classList.add('is-visible');
        }
    }


    getZoomTranslateExtent() {
        const paddingRatio = CONFIG.ZOOM_TRANSLATE_PADDING_RATIO || 0;
        const padding = (this.width || 0) * paddingRatio;
        const plotWidth = this.width || 0;
        return [
            [-padding, -Infinity],
            [plotWidth + padding, Infinity]
        ];
    }

    getSourceEventPosition(sourceEvent) {
        if (!sourceEvent) return null;

        // Handle touch events (prefer current touches; fall back to changed touches)
        if (sourceEvent.touches) {
            if (sourceEvent.touches.length !== 1) {
                return null; // Ignore multi-touch gestures (pinch zoom, etc.)
            }
            const touch = sourceEvent.touches[0];
            return { x: touch.clientX, y: touch.clientY };
        }
        if (sourceEvent.changedTouches) {
            if (sourceEvent.changedTouches.length !== 1) {
                return null;
            }
            const touch = sourceEvent.changedTouches[0];
            return { x: touch.clientX, y: touch.clientY };
        }

        // Pointer and mouse events
        if (typeof sourceEvent.clientX === 'number' && typeof sourceEvent.clientY === 'number') {
            return { x: sourceEvent.clientX, y: sourceEvent.clientY };
        }

        return null;
    }

    handleZoom(event) {
        // Skip if we're in the middle of updating the transform to avoid recursion
        if (this.isUpdatingTransform) {
            return;
        }

        // Get the transform from the zoom event
        const transform = event.transform;

        // Apply transform to xScale domain only (horizontal zoom/pan)
        if (this.originalXDomain && this.actualItemExtent) {
            const [originalMin, originalMax] = this.originalXDomain;
            const [actualMin, actualMax] = this.actualItemExtent;
            const isLinear = this.isLinearScale();

            let domainMin;
            let domainMax;
            let constrained = false;
            const shouldConstrain = !this.isResettingView;
            let originalRange;
            let visibleRange;
            let panOffset;

            if (isLinear) {
                originalRange = originalMax - originalMin;
                visibleRange = originalRange / transform.k;
                panOffset = -(transform.x / this.width) * visibleRange;

                domainMin = originalMin + panOffset;
                domainMax = domainMin + visibleRange;

                if (shouldConstrain) {
                    const actualRange = actualMax - actualMin;
                    if (visibleRange > actualRange) {
                        domainMin = actualMin;
                        domainMax = actualMax;
                        constrained = true;
                    } else if (domainMin < actualMin) {
                        domainMin = actualMin;
                        domainMax = domainMin + visibleRange;
                        constrained = true;
                    } else if (domainMax > actualMax) {
                        domainMax = actualMax;
                        domainMin = domainMax - visibleRange;
                        constrained = true;
                    }
                }
            } else {
                const logOriginalMin = Math.log10(originalMin);
                const logOriginalMax = Math.log10(originalMax);
                originalRange = logOriginalMax - logOriginalMin;

                const logActualMin = Math.log10(actualMin);
                const logActualMax = Math.log10(actualMax);

                visibleRange = originalRange / transform.k;
                panOffset = -(transform.x / this.width) * visibleRange;

                let newLogMin = logOriginalMin + panOffset;
                let newLogMax = newLogMin + visibleRange;

                if (shouldConstrain) {
                    const logItemRange = logActualMax - logActualMin;

                    if (visibleRange > logItemRange) {
                        newLogMin = logActualMin;
                        newLogMax = logActualMax;
                        constrained = true;
                    } else if (newLogMin < logActualMin) {
                        newLogMin = logActualMin;
                        newLogMax = newLogMin + visibleRange;
                        constrained = true;
                    } else if (newLogMax > logActualMax) {
                        newLogMax = logActualMax;
                        newLogMin = newLogMax - visibleRange;
                        constrained = true;
                    }
                }

                domainMin = Math.pow(10, newLogMin);
                domainMax = Math.pow(10, newLogMax);
            }

            // Update xScale domain
            this.xScale.domain([domainMin, domainMax]);

            // If we constrained the domain, we need to decide whether to update the transform
            // Only update the transform when zoomed out (to prevent "stored" zoom)
            // When zoomed in at boundaries, don't update transform to allow further panning
            if (constrained) {
                const constrainedRange = isLinear ? (domainMax - domainMin) : (Math.log10(domainMax) - Math.log10(domainMin));
                const constrainedDomainMin = isLinear ? domainMin : Math.log10(domainMin);
                const originalDomainMin = isLinear ? originalMin : Math.log10(originalMin);
                const constrainedK = originalRange / constrainedRange;
                const constrainedPan = constrainedDomainMin - originalDomainMin;
                const constrainedX = -(constrainedPan / constrainedRange) * this.width;

                const constrainedTransform = d3.zoomIdentity
                    .translate(constrainedX, 0)
                    .scale(constrainedK);

                if (!this.isUpdatingTransform) {
                    this.isUpdatingTransform = true;
                    this.mainGroup.call(this.zoomBehavior.transform, constrainedTransform);
                    this.isUpdatingTransform = false;
                }
            }

            // Throttle plot updates during zoom for better performance on mobile
            // Use requestAnimationFrame to batch updates
            if (!this.zoomUpdatePending) {
                this.zoomUpdatePending = true;
                requestAnimationFrame(() => {
                    this.plot.updatePlotAfterZoom();
                    this.zoomUpdatePending = false;
                });
            }
        }
    }

    // Calculate zoom transform from a domain (used after resize to sync transform with domain)
    calculateTransformFromDomain(domain) {
        if (!this.originalXDomain || !domain) {
            return d3.zoomIdentity;
        }

        const [originalMin, originalMax] = this.originalXDomain;
        const [currentMin, currentMax] = domain;

        let originalRange;
        let currentRange;
        let pan;

        if (this.isLinearScale()) {
            originalRange = originalMax - originalMin;
            currentRange = currentMax - currentMin;
            pan = currentMin - originalMin;
        } else {
            const logOriginalMin = Math.log10(originalMin);
            const logOriginalMax = Math.log10(originalMax);
            originalRange = logOriginalMax - logOriginalMin;

            const logCurrentMin = Math.log10(currentMin);
            const logCurrentMax = Math.log10(currentMax);
            currentRange = logCurrentMax - logCurrentMin;
            pan = logCurrentMin - logOriginalMin;
        }

        const k = originalRange / currentRange;
        const x = -(pan / currentRange) * this.width;

        return d3.zoomIdentity.translate(x, 0).scale(k);
    }


    resetZoom() {
        if (!this.originalXDomain || !this.zoomBehavior) return;

        // Stop any in-progress zoom transitions so reset isn't interrupted
        this.mainGroup.interrupt();

        // Smoothly animate transform back to identity; handleZoom will update the domain
        // based on the zoom transform so we don't need to manually change xScale here.
        const transition = this.mainGroup.transition()
            .duration(CONFIG.RESET_ZOOM_TRANSITION_DURATION)
            .call(this.zoomBehavior.transform, d3.zoomIdentity);

        transition
            .on('start', () => {
                this.isResettingView = true;
            })
            .on('end interrupt', () => {
                this.isResettingView = false;
            });
    }

    setupStickyTopAxis() {
        const plotContainer = document.getElementById('plot-container');
        if (!plotContainer) return;

        // Create container for sticky top axis (exactly like zoom controls)
        let stickyAxisContainer = document.getElementById('sticky-top-axis');
        if (!stickyAxisContainer) {
            stickyAxisContainer = document.createElement('div');
            stickyAxisContainer.id = 'sticky-top-axis';
            stickyAxisContainer.className = 'top-axis-floating';
            document.body.appendChild(stickyAxisContainer);
        }

        // Store reference
        this.stickyAxisContainer = stickyAxisContainer;
        this.stickyAxisSvg = null;

        // Function to update sticky axis container position and size to match plot container
        const updateStickyAxisContainerPosition = () => {
            if (!plotContainer || !stickyAxisContainer) return;

            const plotRect = plotContainer.getBoundingClientRect();
            // Match the plot container's width and horizontal position exactly
            stickyAxisContainer.style.width = `${plotRect.width}px`;
            stickyAxisContainer.style.left = `${plotRect.left}px`;
            stickyAxisContainer.style.right = 'auto'; // Override CSS right: 0
        };

        // Function to update the sticky axis content
        const updateStickyAxis = () => {
            if (!this.xAxisTop || !this.svg || !this.plotContainer) return;

            // Update container position first
            updateStickyAxisContainerPosition();

            // Get the current top axis element
            const topAxisNode = this.xAxisTop.node();
            if (!topAxisNode) return;

            // Get dimensions - use the exact SVG width from the plot for perfect alignment
            // The SVG width is the source of truth for the coordinate system
            const svgWidth = +this.svg.attr('width') || 0;
            // Get the actual rendered container width to calculate scaling ratio
            const plotContainerRect = this.plotContainer.getBoundingClientRect();
            const containerWidth = plotContainerRect.width;
            // Use SVG width for viewBox to match the plot's coordinate system exactly
            // This ensures tick marks align perfectly at all positions
            const viewBoxWidth = svgWidth;
            // Height for axis - need space for text above (with superscripts) and minimal space below
            const svgHeight = 25; // Height for axis (enough for text above, minimal space below)
            const marginLeft = this.margin.left;
            const marginRight = this.margin.right;

            // Create clip path ID for this sticky axis
            const clipId = 'sticky-axis-clip';

            // Create or update the sticky SVG
            // Use the same viewBox dimensions as the plot SVG for perfect alignment
            if (!this.stickyAxisSvg) {
                this.stickyAxisSvg = d3.select(stickyAxisContainer)
                    .append('svg')
                    .attr('width', '100%')
                    .attr('height', svgHeight)
                    .attr('viewBox', `0 0 ${viewBoxWidth} ${svgHeight}`)
                    .attr('preserveAspectRatio', 'none') // Don't preserve aspect ratio - match width exactly
                    .style('display', 'block')
                    .style('overflow', 'hidden'); // Clip content to container width

                // Create clip path to prevent labels from extending beyond container
                // The clip path needs to account for the axis group's transform (marginLeft)
                // Since the group is at translate(marginLeft, svgHeight), the clip path in group coordinates
                // should extend from -marginLeft to (svgWidth - marginLeft) to match the axis domain
                const defs = this.stickyAxisSvg.append('defs');
                defs.append('clipPath')
                    .attr('id', clipId)
                    .append('rect')
                    .attr('x', -marginLeft) // Start from left edge accounting for margin
                    .attr('y', -100) // Allow text above to show
                    .attr('width', svgWidth) // Full width (axis extends from -marginLeft to svgWidth-marginLeft)
                    .attr('height', svgHeight + 100); // Extra height for text above
            } else {
                // Update viewBox to match current container width exactly
                this.stickyAxisSvg
                    .attr('viewBox', `0 0 ${viewBoxWidth} ${svgHeight}`)
                    .attr('height', svgHeight);

                // Update clip path
                const clipRect = this.stickyAxisSvg.select(`#${clipId} rect`);
                if (!clipRect.empty()) {
                    clipRect
                        .attr('x', -marginLeft) // Update x position for margin
                        .attr('width', viewBoxWidth); // Update width to match viewBox
                }
            }

            // Get or create the sticky axis group
            let group = this.stickyAxisSvg.select('.sticky-axis-group');
            if (group.empty()) {
                group = this.stickyAxisSvg.append('g')
                    .attr('class', 'sticky-axis-group')
                    .attr('clip-path', `url(#${clipId})`); // Apply clip path to prevent overflow
            } else {
                // Ensure clip path is applied
                group.attr('clip-path', `url(#${clipId})`);
            }

            // Clear existing content
            group.selectAll('*').remove();

            // Get font size from original axis to match exactly - use the CSS rule value
            // The CSS defines .axis { font-size: 12px; }, so we should use that exact value
            const originalAxisText = this.xAxisTop.select('text');
            let originalFontSize = '12px';
            if (!originalAxisText.empty()) {
                const computedStyle = window.getComputedStyle(originalAxisText.node());
                originalFontSize = computedStyle.fontSize || '12px';
                // Ensure we're using the exact pixel value, not a computed one that might be different
                // Parse the font size to ensure consistency
                const fontSizeMatch = originalFontSize.match(/^([\d.]+)px$/);
                if (fontSizeMatch) {
                    originalFontSize = `${parseFloat(fontSizeMatch[1])}px`;
                }
            }

            // Deep clone all children from the original axis (including text, paths, etc.)
            const cloneNode = (sourceNode) => {
                const cloned = sourceNode.cloneNode(true);
                // Also clone computed styles for text elements
                if (sourceNode.nodeType === 1 && sourceNode.tagName === 'text') {
                    const computedStyle = window.getComputedStyle(sourceNode);
                    // Preserve ALL attributes exactly as they are in the original
                    // This includes x, y, dx, dy, text-anchor, and any other positioning attributes
                    const textAnchor = sourceNode.getAttribute('text-anchor');
                    const x = sourceNode.getAttribute('x');
                    const y = sourceNode.getAttribute('y');
                    const dx = sourceNode.getAttribute('dx');
                    const dy = sourceNode.getAttribute('dy');
                    const transform = sourceNode.getAttribute('transform');

                    // Copy all attributes from source to cloned node first
                    Array.from(sourceNode.attributes).forEach(attr => {
                        // Skip transform, dx, dy as they can interfere with positioning
                        if (attr.name !== 'transform' && attr.name !== 'dx' && attr.name !== 'dy') {
                            cloned.setAttribute(attr.name, attr.value);
                        }
                    });

                    // Override with computed styles for fill and font properties
                    cloned.setAttribute('fill', computedStyle.fill || 'var(--text-secondary)');
                    cloned.setAttribute('font-size', originalFontSize); // Use exact font size
                    cloned.setAttribute('font-family', computedStyle.fontFamily || 'inherit');

                    // CRITICAL: For axisTop, text MUST be centered on tick marks
                    // D3 axisTop sets text-anchor to 'middle' and x to the tick position
                    // We must preserve x exactly and ensure text-anchor is 'middle'
                    cloned.setAttribute('text-anchor', 'middle'); // Force middle alignment for centering

                    // Preserve x, y exactly as they are (x should be the tick position)
                    // x coordinate is the center point when text-anchor is 'middle'
                    if (x !== null && x !== undefined) cloned.setAttribute('x', x);
                    if (y !== null && y !== undefined) cloned.setAttribute('y', y);

                    // Remove dx, dy, and transform to ensure no offset from centering
                    cloned.removeAttribute('dx');
                    cloned.removeAttribute('dy');
                    cloned.removeAttribute('transform');
                }
                // Clone stroke styles for lines/paths to match plot axis styling
                if (sourceNode.nodeType === 1 && (sourceNode.tagName === 'path' || sourceNode.tagName === 'line')) {
                    const computedStyle = window.getComputedStyle(sourceNode);
                    cloned.setAttribute('stroke', computedStyle.stroke || 'var(--border-color)');
                    cloned.setAttribute('stroke-width', computedStyle.strokeWidth || sourceNode.getAttribute('stroke-width') || '1');
                }
                return cloned;
            };

            // Clone all children from the original axis
            Array.from(topAxisNode.childNodes).forEach(child => {
                if (child.nodeType === 1) { // Element node
                    const cloned = cloneNode(child);
                    group.node().appendChild(cloned);

                    // For text elements, ensure text-anchor is explicitly set to 'middle' after cloning
                    // This ensures centering even if the original had a different value
                    if (child.tagName === 'text') {
                        cloned.setAttribute('text-anchor', 'middle');
                        // Also ensure no dx/dy/transform that could shift the text
                        cloned.removeAttribute('dx');
                        cloned.removeAttribute('dy');
                        cloned.removeAttribute('transform');
                    }
                }
            });

            // Position the axis group to match the plot axis horizontally
            // Vertically, position so the axis line (at y=0 in the cloned group) is at axisLineY
            // This puts the axis line near the bottom with minimal space below, and space above for text
            group.attr('transform', `translate(${marginLeft},${svgHeight})`);

            // Update the domain line to match the plot axis exactly
            // The plot axis domain goes from -marginLeft to (viewBoxWidth - marginLeft)
            // This matches what we set in plot.js, but using viewBoxWidth for exact alignment
            const axisLeft = -marginLeft;
            const axisRight = viewBoxWidth - marginLeft;
            const domainLine = group.select('.domain');
            if (!domainLine.empty()) {
                domainLine.attr('d', `M${axisLeft},0H${axisRight}`);
            }

            // Apply axis styling to match plot axes
            // Use computed styles from the original axis to get actual color values
            const originalDomainLine = this.xAxisTop.select('.domain');
            if (!originalDomainLine.empty()) {
                const originalStroke = window.getComputedStyle(originalDomainLine.node()).stroke;
                group.selectAll('path.domain, line').style('stroke', originalStroke);
            }
            const originalAxisTextForFill = this.xAxisTop.select('text');
            if (!originalAxisTextForFill.empty()) {
                const originalFill = window.getComputedStyle(originalAxisTextForFill.node()).fill;
                group.selectAll('text').style('fill', originalFill);
            }
        };

        // Store update function
        this.updateStickyAxis = updateStickyAxis;

        // Function to check visibility and update sticky axis
        const checkVisibility = () => {
            if (this.experiences?.active) {
                stickyAxisContainer.classList.remove('is-visible');
                return;
            }
            const plotRect = plotContainer.getBoundingClientRect();
            const stickyRect = stickyAxisContainer.getBoundingClientRect();
            const stickyAxisHeight = stickyRect.height || 30; // Height of sticky axis

            // Get the bottom axis position within the plot container
            // The bottom axis is at the bottom of the plot area (yScale(0))
            // We need to check if the sticky axis would overlap with the bottom axis
            const plotContainerTop = plotRect.top;
            const plotContainerBottom = plotRect.bottom;
            const plotContainerHeight = plotRect.height;

            // The bottom axis is at the bottom of the plot container
            // Calculate where the bottom axis would be in viewport coordinates
            // The bottom axis is typically near the bottom of the plot container
            // We'll hide the sticky axis when it would overlap with the bottom axis area
            const bottomAxisApproxY = plotContainerBottom - 20; // Approximate bottom axis position (margin.bottom)

            // Show sticky axis when:
            // 1. Plot container top is scrolled above viewport (top axis not visible)
            // 2. Sticky axis bottom (viewport top + sticky height) is above the bottom axis
            const stickyAxisBottom = stickyAxisHeight; // Sticky axis bottom is at viewport top + height
            const shouldShow = plotContainerTop < 0 && stickyAxisBottom < bottomAxisApproxY;

            if (shouldShow) {
                // Plot container top is above viewport and sticky axis won't overlap with bottom axis
                if (!stickyAxisContainer.classList.contains('is-visible')) {
                    stickyAxisContainer.classList.add('is-visible');
                    updateStickyAxis();
                }
            } else {
                // Either plot container top is visible (top axis visible) or sticky would overlap bottom axis
                stickyAxisContainer.classList.remove('is-visible');
            }
        };

        // Use IntersectionObserver to show/hide sticky axis
        // Show when plot container's top axis is scrolled out of view (when top of plot container is above viewport)
        // Hide when the plot container's top is visible (meaning the top axis within the plot is visible)
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    checkVisibility();
                });
            }, {
                root: null,
                threshold: [0], // Trigger when top edge crosses viewport
                rootMargin: '0px'
            });
            observer.observe(plotContainer);
        }

        // Also use scroll listener as backup to ensure responsiveness
        window.addEventListener('scroll', checkVisibility, { passive: true });

        // Check initial state immediately and after a short delay to ensure DOM is ready
        checkVisibility();
        setTimeout(checkVisibility, 100);

        // Update position on window resize
        window.addEventListener('resize', () => {
            if (stickyAxisContainer.classList.contains('is-visible')) {
                updateStickyAxis();
            }
        }, { passive: true });
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new UniversalScales();
});
