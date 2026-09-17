// Universal Scales - Plot Rendering Module
// Handles all D3.js plot rendering, item drawing, axes, grid, and positioning

class PlotRenderer {
    constructor(app) {
        this.app = app; // Reference to main UniversalScales instance
        
        // D3.js setup - these will be initialized in initPlot
        this.margin = CONFIG.MARGIN;
        this.width = 0;
        this.height = 0;
        this.svg = null;
        this.xScale = null;
        this.yScale = null;
        this.originalXDomain = null; // Store original domain for zoom reset
        this.axisClipId = `axis-clip-${Math.random().toString(36).slice(2)}`;
        this.axisClipRect = null;
        this.itemsClipId = `items-clip-${Math.random().toString(36).slice(2)}`;
        this.itemsClipRect = null;
        this.lastTickSet = null; // Store last tick set for stability
        this.lastTickDomain = null; // Store domain when ticks were last calculated
        this.lastTickLogRange = null; // Store log range for zoom level tracking
        this.actualItemExtent = null; // Store actual item extent (for zoom limits)
        this.originalItemsHeight = null; // Store original itemsHeight to preserve vertical layout when zoomed
        this.xScaleMode = 'log';
    }
    
    initPlot() {
        this.updateDimensions();
        
        // Get container width directly to ensure SVG matches exactly
        const containerRect = this.app.plotContainer.getBoundingClientRect();
        const containerWidth = containerRect.width;
        const containerHeight = containerRect.height;
        
        this.svg = d3.select('#plot-svg')
            .attr('width', containerWidth)
            .attr('height', containerHeight)
            .style('overflow', 'visible'); // Allow labels to extend beyond SVG bounds
        
        // Create defs and clip paths
        this.defs = this.svg.append('defs');
        
        // Clip path for axes and grid
        this.axisClipRect = this.defs.append('clipPath')
            .attr('id', this.axisClipId)
            .append('rect');
        this.updateAxisClip();
        
        // Clip path for items to prevent overflow
        this.itemsClipRect = this.defs.append('clipPath')
            .attr('id', this.itemsClipId)
            .append('rect');
        this.updateItemsClip();
        
        // Create main group
        this.mainGroup = this.svg.append('g')
            .attr('transform', `translate(${this.margin.left},${this.margin.top})`)
            .attr('clip-path', `url(#${this.itemsClipId})`);
        
        // Create scales
        this.ensureXScaleMode('log');
        
        this.yScale = d3.scaleLinear()
            .range([this.height, 0]);
        
        // Add axes with clip path to prevent labels from extending beyond container
        this.xAxis = this.mainGroup.append('g')
            .attr('class', 'axis')
            .attr('transform', `translate(0,${this.height})`)
            .attr('clip-path', `url(#${this.axisClipId})`)
            .style('pointer-events', 'none'); // Don't block zoom events
        
        this.xAxisTop = this.mainGroup.append('g')
            .attr('class', 'axis')
            .attr('transform', `translate(0,0)`)
            .attr('clip-path', `url(#${this.axisClipId})`)
            .style('pointer-events', 'none'); // Don't block zoom events
        
        // Create background rectangle for top axis (to cover items when axis moves down)
        // Will be created/positioned in drawItems to ensure it's above items but below axis
        this.xAxisTopBackground = null; // Will be created when needed
        
        // Add grid lines (no clip path needed - they're within plot area)
        this.gridGroup = this.mainGroup.append('g')
            .attr('class', 'grid')
            .style('pointer-events', 'none'); // Don't block zoom events
        
        // Store references in app for zoom/other functionality
        this.app.svg = this.svg;
        this.app.xScale = this.xScale;
        this.app.yScale = this.yScale;
        this.app.mainGroup = this.mainGroup;
        this.app.originalXDomain = this.originalXDomain;
        this.app.actualItemExtent = this.actualItemExtent;
        this.app.xAxis = this.xAxis;
        this.app.xAxisTop = this.xAxisTop;
    }
    
    updateAxisClip() {
        if (!this.axisClipRect || !this.svg) return;
        // Use SVG dimensions to ensure clip covers full SVG (which matches container)
        // Clip paths are relative to the element they're applied to, so coordinates
        // need to account for the mainGroup translation
        const svgWidth = +this.svg.attr('width') || 0;
        const svgHeight = +this.svg.attr('height') || 0;
        
        // Only update if we have valid dimensions
        if (svgWidth > 0 && svgHeight > 0) {
            this.axisClipRect
                .attr('x', -this.margin.left)
                .attr('y', -this.margin.top)
                .attr('width', svgWidth)
                .attr('height', svgHeight);
        }
    }
    
    updateItemsClip() {
        if (!this.itemsClipRect || !this.svg) return;
        // Clip items to the full container (including margins) so plot edge matches container
        const svgWidth = +this.svg.attr('width') || 0;
        const svgHeight = +this.svg.attr('height') || 0;
        
        // Clip path coordinates are relative to mainGroup (which is translated by margins)
        // So we need to account for that translation
        if (svgWidth > 0 && svgHeight > 0) {
            this.itemsClipRect
                .attr('x', -this.margin.left)
                .attr('y', -this.margin.top)
                .attr('width', svgWidth)
                .attr('height', svgHeight);
        }
    }
    
    updateDimensions() {
        const containerRect = this.app.plotContainer.getBoundingClientRect();
        // Calculate plot area dimensions (excluding margins)
        // Ensure width and height are never negative
        this.width = Math.max(0, containerRect.width - this.margin.left - this.margin.right);
        this.height = Math.max(0, containerRect.height - this.margin.top - this.margin.bottom);
        
        // Update SVG dimensions to match container exactly
        if (this.svg) {
            this.svg
                .attr('width', containerRect.width)
                .attr('height', containerRect.height);
        }
        
        // Update app references
        this.app.width = this.width;
        this.app.height = this.height;
    }

    getScaleMode() {
        return this.app.dimensionData?.scale_mode === 'linear' ? 'linear' : 'log';
    }

    isLinearScale() {
        return this.getScaleMode() === 'linear';
    }

    ensureXScaleMode(mode = this.getScaleMode()) {
        if (this.xScale && this.xScaleMode === mode) {
            this.xScale.range([0, this.width]);
            this.app.xScale = this.xScale;
            return;
        }

        this.xScaleMode = mode;
        this.xScale = mode === 'linear'
            ? d3.scaleLinear().range([0, this.width])
            : d3.scaleLog().range([0, this.width]);

        this.app.xScale = this.xScale;
        this.lastTickSet = null;
        this.lastTickDomain = null;
        this.lastTickLogRange = null;
    }

    domainChangedSignificantly(currentDomain, nextDomain) {
        if (!currentDomain || !nextDomain) return true;
        const delta = Math.max(
            Math.abs(currentDomain[0] - nextDomain[0]),
            Math.abs(currentDomain[1] - nextDomain[1])
        );
        const scale = Math.max(
            Math.abs(nextDomain[0]),
            Math.abs(nextDomain[1]),
            Math.abs(nextDomain[1] - nextDomain[0]),
            1
        );
        return (delta / scale) > CONFIG.DOMAIN_CHANGE_THRESHOLD;
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

    extendDomain(extent) {
        const [minValue, maxValue] = extent;
        if (this.isLinearScale()) {
            const range = maxValue - minValue;
            const basis = range > 0 ? range : Math.max(Math.abs(minValue), Math.abs(maxValue), 1);
            const padding = basis * CONFIG.LINEAR_EXTENT_PADDING_RATIO;
            return [minValue - padding, maxValue + padding];
        }

        return [minValue * CONFIG.EXTENT_LOWER_MULTIPLIER, maxValue * CONFIG.EXTENT_UPPER_MULTIPLIER];
    }
    
    generateAxisTicks() {
        if (this.isLinearScale()) {
            return this.generateLinearTicks();
        }
        return this.generatePowerOfTenTicks();
    }

    generateLinearTicks() {
        const [min, max] = this.xScale.domain();
        const minLabelSpacing = window.matchMedia(`(max-width: ${CONFIG.MOBILE_BREAKPOINT}px)`).matches
            ? CONFIG.LABEL_SPACING_MOBILE
            : CONFIG.LABEL_SPACING_DESKTOP;
        const maxByWidth = Math.max(CONFIG.TICK_MIN_COUNT, Math.floor(this.width / minLabelSpacing));
        const targetCount = Math.max(CONFIG.TICK_MIN_COUNT, Math.min(CONFIG.AXIS_TICKS, maxByWidth));
        const ticks = this.xScale.ticks(targetCount).filter(Number.isFinite);
        if (ticks.length > 0) {
            return ticks;
        }
        return [min, max].filter(Number.isFinite);
    }

    generatePowerOfTenTicks() {
        // Get the current domain
        const [min, max] = this.xScale.domain();
        
        // Convert to log space to find the power-of-10 range
        const logMin = Math.log10(min);
        const logMax = Math.log10(max);
        const logRange = logMax - logMin;
        
        // Calculate container bounds (including margins) early so both reuse and main paths can use them
        // Return ticks that would be visible in the container (including margins)
        // For a log scale: x = (log(domain) - log(min)) / (log(max) - log(min)) * width
        // So: log(domain) = log(min) + (x / width) * logRange
        // The container extends from -margin.left to width + margin.right in mainGroup coordinates
        // xScale maps [min, max] to [0, width], so we extrapolate for margins
        let containerMinDomain = min;
        let containerMaxDomain = max;
        
        if (this.width > 0 && logRange > 0) {
            // Calculate what domain values map to the container edges
            // Left edge: x = -margin.left
            const leftEdgeLog = logMin + (-this.margin.left / this.width) * logRange;
            containerMinDomain = Math.pow(10, leftEdgeLog);
            
            // Right edge: x = width + margin.right
            const rightEdgeLog = logMax + (this.margin.right / this.width) * logRange;
            containerMaxDomain = Math.pow(10, rightEdgeLog);
        }
        
        // Check if we should reuse the last tick set (for seamless panning)
        // If zoom level hasn't changed, we're just panning - reuse the same tick set
        if (this.lastTickSet && this.lastTickLogRange !== null) {
            // Check if zoom level has changed significantly
            const relativeChange = Math.abs(logRange - this.lastTickLogRange) / Math.max(logRange, this.lastTickLogRange);
            const zoomLevelChanged = relativeChange > CONFIG.TICK_ZOOM_LEVEL_CHANGE_THRESHOLD;
            
            // If zoom level hasn't changed, we're panning - reuse the tick set and filter to container bounds
            if (!zoomLevelChanged) {
                // Filter to container bounds (including margins) not just visible domain
                const ticksInContainer = this.lastTickSet.filter(tick => tick >= containerMinDomain && tick <= containerMaxDomain);
                if (ticksInContainer.length >= CONFIG.TICK_MIN_COUNT) {
                    const firstTick = ticksInContainer[0];
                    const lastTick = ticksInContainer[ticksInContainer.length - 1];
                    const firstIndex = this.lastTickSet.indexOf(firstTick);
                    const lastIndex = this.lastTickSet.indexOf(lastTick);
                    const bufferStart = Math.max(0, firstIndex - 1);
                    const bufferEnd = Math.min(this.lastTickSet.length - 1, lastIndex + 1);
                    const ticksWithBuffer = this.lastTickSet.slice(bufferStart, bufferEnd + 1);
                    
                    if (this.lastTickDomain) {
                        this.lastTickDomain = [min, max];
                    }
                    return ticksWithBuffer;
                }
            }
            // If zoom level changed, continue to generate new ticks below
        }
        
        // Calculate target density based on the CURRENT visible range
        const minLabelSpacing = window.matchMedia(`(max-width: ${CONFIG.MOBILE_BREAKPOINT}px)`).matches 
            ? CONFIG.LABEL_SPACING_MOBILE 
            : CONFIG.LABEL_SPACING_DESKTOP;
        const maxByWidth = Math.max(CONFIG.TICK_MIN_COUNT, Math.floor(this.width / minLabelSpacing));
        const targetCount = Math.max(CONFIG.TICK_MIN_COUNT, Math.min(CONFIG.AXIS_TICKS, maxByWidth));
        
        // First, generate ticks for the visible range to determine density
        const visibleMinPower = Math.floor(logMin);
        const visibleMaxPower = Math.ceil(logMax);
        const visiblePowerOfTenTicks = [];
        for (let power = visibleMinPower; power <= visibleMaxPower; power++) {
            const value = Math.pow(10, power);
            if (value >= min && value <= max) {
                visiblePowerOfTenTicks.push(value);
            }
        }
        const visibleTickCount = visiblePowerOfTenTicks.length;
        
        // Determine step size based on visible range needs
        let step = 1;
        if (visibleTickCount > targetCount) {
            step = Math.ceil(visibleTickCount / targetCount);
        }
        
        // Generate ticks for the FULL item range (from lowest to highest item)
        // This ensures ticks are available when panning to any part of the data
        let fullRangeMin, fullRangeMax;
        if (this.actualItemExtent) {
            // Use actual item extent, with lower bound extended for label space (same as plot domain)
            const [itemMin, itemMax] = this.actualItemExtent;
            fullRangeMin = itemMin * CONFIG.EXTENT_LOWER_MULTIPLIER;
            fullRangeMax = itemMax * CONFIG.EXTENT_UPPER_MULTIPLIER; // Match the extended extent used in updatePlot
        } else {
            // Fallback: use current domain if item extent not available yet
            fullRangeMin = min;
            fullRangeMax = max;
        }
        
        const fullLogMin = Math.log10(fullRangeMin);
        const fullLogMax = Math.log10(fullRangeMax);
        const minPower = Math.floor(fullLogMin);
        const maxPower = Math.ceil(fullLogMax);
        
        // Generate all powers of 10 in the full item range
        const allPowerOfTenTicks = [];
        for (let power = minPower; power <= maxPower; power++) {
            const value = Math.pow(10, power);
            allPowerOfTenTicks.push(value);
        }
        
        // Apply the step to maintain density (same as visible range)
        // Always start from the beginning of the full range to ensure consistent coverage
        // This ensures ticks are available when panning in any direction
        let filteredTicks = allPowerOfTenTicks;
        if (step > 1) {
            // Start from the beginning (index 0) to ensure consistent pattern throughout
            // This way, when panning left or right, the tick pattern is always consistent
            filteredTicks = [];
            for (let i = 0; i < allPowerOfTenTicks.length; i += step) {
                filteredTicks.push(allPowerOfTenTicks[i]);
            }
        }
        
        // Store the FULL filtered tick set (for the full item range) for seamless panning
        // This set covers from the lowest to highest item, so ticks are always available when panning
        this.lastTickSet = filteredTicks;
        this.lastTickDomain = [min, max];
        this.lastTickLogRange = logRange;
        
        // Filter ticks that fall within the container domain range (container bounds already calculated above)
        const visibleTicks = filteredTicks.filter(tick => {
            return tick >= containerMinDomain && tick <= containerMaxDomain;
        });
        
        // If we have valid ticks, return them; otherwise return a safe subset
        if (visibleTicks.length > 0) {
            return visibleTicks;
        }
        
        // Fallback: return ticks in the visible domain if no ticks are in container bounds
        // This can happen at extreme zoom levels
        return filteredTicks.filter(tick => tick >= min && tick <= max);
    }
    
    updateGrid() {
        this.gridGroup.selectAll('.grid-line').remove();
        
        // Vertical grid lines - use the same tick values as axes for consistency
        const tickValues = this.generateAxisTicks();
        const yDomain = this.yScale.domain();
        const yTop = this.yScale(yDomain[1]);
        const yBottom = this.yScale(0);
        this.gridGroup.selectAll('.grid-line-x')
            .data(tickValues)
            .enter().append('line')
            .attr('class', 'grid-line')
            .attr('x1', d => this.xScale(d))
            .attr('x2', d => this.xScale(d))
            .attr('y1', yTop) // Top horizontal axis
            .attr('y2', yBottom) // Bottom horizontal axis
            .style('pointer-events', 'none'); // Don't block zoom events
        
        // Horizontal grid lines (simplified)
        // Extend to full container width
        const svgWidth = +this.svg.attr('width') || 0;
        const gridLeft = -this.margin.left;
        const gridRight = svgWidth - this.margin.left;
        const yTicks = this.yScale.ticks(CONFIG.GRID_TICKS);
        this.gridGroup.selectAll('.grid-line-y')
            .data(yTicks)
            .enter().append('line')
            .attr('class', 'grid-line')
            .attr('x1', gridLeft)
            .attr('x2', gridRight)
            .attr('y1', d => this.yScale(d))
            .attr('y2', d => this.yScale(d))
            .style('pointer-events', 'none'); // Don't block zoom events
    }
    
    positionItems(items) {
        // Sort items by value (smallest to largest)
        const sortedItems = [...items].sort((a, b) => a.convertedValue - b.convertedValue);
        
        // Use fixed vertical spacing for consistent visual appearance
        const positionedItems = [];
        
        sortedItems.forEach((item, index) => {
            // Calculate absolute pixel position from bottom
            const yPosition = CONFIG.BOTTOM_PADDING + (index * CONFIG.FIXED_VERTICAL_SPACING);
            
            positionedItems.push({
                ...item,
                yPosition: yPosition,
                xOffset: 0 // Will be calculated later after scale domain is set
            });
        });
        
        return positionedItems;
    }
    
    calculateHorizontalOffsets(positionedItems) {
        // Add horizontal buffer for points near the left edge to prevent text overflow
        positionedItems.forEach(item => {
            const xPosition = this.xScale(item.convertedValue);
            const estimatedTextWidth = item.name.length * CONFIG.TEXT_WIDTH_ESTIMATE;
            const minXPosition = estimatedTextWidth + CONFIG.TEXT_BUFFER;
            
            // Only apply offset if the point would cause text overflow
            // Use a more conservative approach - don't double the buffer for lowest point
            if (xPosition < minXPosition) {
                item.xOffset = minXPosition - xPosition;
            }
        });
        
        return positionedItems;
    }
    
    drawItems(positionedItems) {
        // Draw vertical lines first (behind everything else)
        const verticalLinesGroup = this.mainGroup.append('g')
            .attr('class', 'vertical-lines-group');
        const yDomain = this.yScale.domain();
        const yTop = this.yScale(yDomain[1]);
        const yBottom = this.yScale(0);
        
        verticalLinesGroup.selectAll('.vertical-line')
            .data(positionedItems)
            .enter().append('line')
            .attr('class', 'vertical-line')
            .attr('x1', d => this.xScale(d.convertedValue))
            .attr('x2', d => this.xScale(d.convertedValue))
            .attr('y1', yTop) // Align with top horizontal axis
            .attr('y2', yBottom) // Align with bottom horizontal axis
            .attr('stroke', CONFIG.POINT_FILL_COLOR)
            .attr('stroke-width', CONFIG.VERTICAL_LINE_STROKE_WIDTH)
            .attr('stroke-opacity', CONFIG.VERTICAL_LINE_OPACITY)
            .attr('stroke-dasharray', CONFIG.VERTICAL_LINE_DASH_ARRAY)
            .attr('pointer-events', 'none'); // Disable pointer events on line
        
        const itemGroup = this.mainGroup.selectAll('.item-group')
            .data(positionedItems)
            .enter().append('g')
            .attr('class', 'item-group')
            .attr('transform', d => {
                const x = this.xScale(d.convertedValue); // Keep points at true position
                // Use yScale to convert yPosition (in domain units) to screen coordinates
                // This ensures consistent positioning even when height changes
                const y = this.yScale(d.yPosition);
                return `translate(${x},${y})`;
            });
        
        // Item circles
        const circle = itemGroup.append('circle')
            .attr('class', 'plot-item')
            .attr('r', CONFIG.POINT_RADIUS)
            .attr('fill', CONFIG.POINT_FILL_COLOR)
            .attr('stroke', CONFIG.POINT_STROKE_COLOR)
            .attr('stroke-width', CONFIG.POINT_STROKE_WIDTH)
            .attr('pointer-events', 'none'); // Disable pointer events on circle

        // On touch devices, add a generous invisible tap target around each item
        if (('ontouchstart' in window) || window.matchMedia('(hover: none)').matches) {
            const tapTarget = itemGroup.append('circle')
                .attr('class', 'tap-target')
                .attr('r', CONFIG.TAP_TARGET_RADIUS) // larger hit area for fingers
                .attr('fill', 'transparent')
                .attr('pointer-events', 'all')
                .on('pointerdown', (event) => {
                    // Store initial position for drag detection
                    event.target.setAttribute('data-touch-start-x', event.clientX);
                    event.target.setAttribute('data-touch-start-y', event.clientY);
                    event.target.setAttribute('data-was-drag', 'false');
                })
                .on('pointermove', (event) => {
                    // Detect if this is a drag
                    const startX = parseFloat(event.target.getAttribute('data-touch-start-x') || '0');
                    const startY = parseFloat(event.target.getAttribute('data-touch-start-y') || '0');
                    const moveDistance = Math.sqrt(
                        Math.pow(event.clientX - startX, 2) + 
                        Math.pow(event.clientY - startY, 2)
                    );
                    if (moveDistance > CONFIG.MAX_CLICK_DISTANCE * 2) {
                        event.target.setAttribute('data-was-drag', 'true');
                    }
                })
                .on('pointerup', (event, d) => {
                    // Only show tooltip if it wasn't a drag
                    const wasDrag = event.target.getAttribute('data-was-drag') === 'true';
                    if (!wasDrag) {
                        event.preventDefault();
                        event.stopPropagation();
                        this.app.showTooltip(event, d);
                    }
                    // Clean up
                    event.target.removeAttribute('data-touch-start-x');
                    event.target.removeAttribute('data-touch-start-y');
                    event.target.removeAttribute('data-was-drag');
                });
        }
        
        // Item labels with smart positioning and invisible hover area
        const labelGroup = itemGroup.append('g')
            .attr('class', 'label-group');
        
        // Add invisible rectangle for hover/tap detection that encompasses both circle and text
        labelGroup.append('rect')
            .attr('class', 'label-hover-area')
            .attr('x', d => {
                const estimatedTextWidth = d.name.length * CONFIG.TEXT_WIDTH_ESTIMATE;
                // Position to the left of the circle, same as text
                return CONFIG.LABEL_OFFSET_X - estimatedTextWidth;
            })
            .attr('y', () => {
                // Slightly enlarge vertical hitbox on small screens
                return window.matchMedia(`(max-width: ${CONFIG.MOBILE_BREAKPOINT}px)`).matches 
                    ? (CONFIG.LABEL_OFFSET_Y + CONFIG.LABEL_OFFSET_Y_MOBILE_ADJUSTMENT) 
                    : CONFIG.LABEL_OFFSET_Y;
            }) // Start above the circle
            .attr('width', d => {
                const estimatedTextWidth = d.name.length * CONFIG.TEXT_WIDTH_ESTIMATE;
                // Total width: text width + padding + circle diameter + padding
                return estimatedTextWidth + CONFIG.LABEL_PADDING + (CONFIG.POINT_RADIUS * 2) + CONFIG.LABEL_CIRCLE_PADDING;
            })
            .attr('height', () => {
                return window.matchMedia(`(max-width: ${CONFIG.MOBILE_BREAKPOINT}px)`).matches 
                    ? Math.max(CONFIG.LABEL_HEIGHT_MOBILE_MIN, CONFIG.LABEL_HEIGHT) 
                    : CONFIG.LABEL_HEIGHT;
            }) // Height to encompass circle and text
            .attr('fill', 'transparent')
            .attr('cursor', 'pointer')
            .on('pointerdown', (event, d) => {
                // Store that pointerdown occurred on this element
                // Use a data attribute to track which element was clicked
                event.target.setAttribute('data-pointer-down', 'true');
                // Store initial position to detect drag
                event.target.setAttribute('data-pointer-down-x', event.clientX);
                event.target.setAttribute('data-pointer-down-y', event.clientY);
                event.target.setAttribute('data-was-drag', 'false');
            })
            .on('pointermove', (event) => {
                // Detect if this is a drag (on mobile)
                const isMobile = ('ontouchstart' in window) || window.matchMedia('(hover: none)').matches;
                if (isMobile) {
                    const downX = parseFloat(event.target.getAttribute('data-pointer-down-x') || '0');
                    const downY = parseFloat(event.target.getAttribute('data-pointer-down-y') || '0');
                    const moveDistance = Math.sqrt(
                        Math.pow(event.clientX - downX, 2) + 
                        Math.pow(event.clientY - downY, 2)
                    );
                    if (moveDistance > CONFIG.MAX_CLICK_DISTANCE * 2) {
                        event.target.setAttribute('data-was-drag', 'true');
                    }
                }
            })
            .on('pointerenter', (event, d) => {
                if (window.matchMedia('(hover: hover)').matches) {
                    // Don't show hover tooltip if a tooltip is already pinned
                    if (!this.app.tooltipPinned) {
                        this.app.showTooltip(event, d);
                        const itemGroupElement = event.target.closest('.item-group');
                        if (itemGroupElement) {
                            d3.select(itemGroupElement).select('circle')
                                .transition()
                                .duration(CONFIG.HOVER_TRANSITION_DURATION)
                                .attr('r', CONFIG.POINT_RADIUS_HOVER)
                                .attr('stroke-width', CONFIG.POINT_STROKE_WIDTH_HOVER);
                        }
                    }
                }
            })
            .on('pointerleave', (event) => {
                if (window.matchMedia('(hover: hover)').matches) {
                    // Don't hide tooltip if it's pinned (clicked on desktop)
                    if (!this.app.tooltipPinned) {
                        this.app.hideTooltip();
                    }
                    const itemGroupElement = event.target.closest('.item-group');
                    if (itemGroupElement) {
                        d3.select(itemGroupElement).select('circle')
                            .transition()
                            .duration(CONFIG.HOVER_TRANSITION_DURATION)
                            .attr('r', CONFIG.POINT_RADIUS)
                            .attr('stroke-width', CONFIG.POINT_STROKE_WIDTH);
                    }
                }
                // Clear pointerdown flag when leaving the element
                event.target.removeAttribute('data-pointer-down');
            })
            .on('pointerup', (event, d) => {
                const pointerType = (event.pointerType || '').toLowerCase();
                const isTouchPointer = pointerType === 'touch' || pointerType === 'pen';
                const isTouchPrimary = isTouchPointer || window.matchMedia('(hover: none)').matches;
                const wasDrag = event.target.getAttribute('data-was-drag') === 'true';
                
                // On mobile, only show tooltip if it wasn't a drag
                if (isTouchPrimary && !wasDrag) {
                    event.preventDefault();
                    event.stopPropagation();
                    this.app.showTooltip(event, d);
                } else if (!isTouchPrimary) {
                    // Desktop: Show and pin tooltip on click (instead of opening source directly)
                    // Only if pointerdown also occurred on this element and the pointer didn't move too far
                    const wasPointerDown = event.target.getAttribute('data-pointer-down') === 'true';
                    const downX = parseFloat(event.target.getAttribute('data-pointer-down-x') || '0');
                    const downY = parseFloat(event.target.getAttribute('data-pointer-down-y') || '0');
                    const moveDistance = Math.sqrt(
                        Math.pow(event.clientX - downX, 2) + 
                        Math.pow(event.clientY - downY, 2)
                    );
                    if (wasPointerDown && moveDistance <= CONFIG.MAX_CLICK_DISTANCE) {
                        event.preventDefault();
                        event.stopPropagation();
                        // Show tooltip pinned so it stays on screen and source link is clickable
                        this.app.showTooltip(event, d, true);
                    }
                }
                // Clear pointerdown flag after handling
                event.target.removeAttribute('data-pointer-down');
                event.target.removeAttribute('data-pointer-down-x');
                event.target.removeAttribute('data-pointer-down-y');
                event.target.removeAttribute('data-was-drag');
            });
        
        // Add the actual text with smart positioning
        labelGroup.append('text')
            .attr('class', 'item-label')
            .attr('x', CONFIG.LABEL_OFFSET_X) // Keep text at consistent distance from point
            .attr('dy', 0)
            .attr('font-size', CONFIG.LABEL_FONT_SIZE)
            .attr('fill', 'currentColor')
            .attr('text-anchor', 'end') // Right-align text since it's to the left of the point
            .attr('dominant-baseline', 'central')
            .attr('pointer-events', 'none')
            .text(d => d.name);
    }
    
    updatePlot() {
        if (!this.app.dimensionData) return;
        if (this.app.experiences?.active) { this.app.experiences.refresh(); return; }
        
        // Clear existing plot elements
        this.mainGroup.selectAll('.item-group').remove();
        this.mainGroup.selectAll('.vertical-lines-group').remove();
        
        // Get all items
        const allItems = this.app.getAllItems();
        this.ensureXScaleMode();
        
        // Update scales
        const values = allItems.map(item => item.convertedValue);
        const extent = d3.extent(values);
        
        // Store actual item extent (for zoom limits)
        this.actualItemExtent = [...extent];
        this.app.actualItemExtent = this.actualItemExtent;
        
        const extendedExtent = this.extendDomain(extent);
        
        // Store original domain for zoom reset
        // Reset original domain when dimension/unit changes (check if domain changed significantly)
        const currentDomain = this.xScale.domain();
        if (!this.originalXDomain || 
            this.domainChangedSignificantly(currentDomain, extendedExtent)) {
            // Domain changed significantly, reset zoom
            this.originalXDomain = [...extendedExtent];
            this.xScale.domain(extendedExtent);
            // Reset zoom transform to identity
            if (this.app.zoomBehavior) {
                this.mainGroup.call(this.app.zoomBehavior.transform, d3.zoomIdentity);
            }
        } else {
            // Check if currently zoomed
            const isZoomed = this.isDomainZoomed(currentDomain, this.originalXDomain);
            
            if (!isZoomed) {
                // Not zoomed, use original domain
                this.xScale.domain(extendedExtent);
            }
            // If zoomed, keep current domain
        }
        
        // Update app references
        this.app.originalXDomain = this.originalXDomain;
        
        // Position items with collision avoidance
        const positionedItems = this.positionItems(allItems);
        
        // Calculate horizontal offsets after scale domain is set
        this.calculateHorizontalOffsets(positionedItems);
        
        // Calculate dynamic SVG height based on number of items with fixed spacing
        const numItems = allItems.length;
        
        // Calculate required height for items using fixed spacing
        const itemsHeight = (numItems > 0) ? CONFIG.BOTTOM_PADDING + ((numItems - 1) * CONFIG.FIXED_VERTICAL_SPACING) + CONFIG.TOP_PADDING : CONFIG.BOTTOM_PADDING + CONFIG.TOP_PADDING;
        
        // Store original itemsHeight to preserve vertical layout when zoomed and resizing
        this.originalItemsHeight = itemsHeight;
        this.app.originalItemsHeight = itemsHeight;
        
        // Calculate total SVG height (items + margins)
        const requiredSvgHeight = itemsHeight + this.margin.top + this.margin.bottom;
        const svgHeight = Math.max(CONFIG.MIN_SVG_HEIGHT, requiredSvgHeight);
        
        // Update SVG height (width is handled by updateDimensions)
        // Ensure updateDimensions is called to sync SVG width with container
        this.updateDimensions();
        this.svg.attr('height', svgHeight);
        
        // Update inner plot height
        this.height = svgHeight - this.margin.top - this.margin.bottom;
        this.app.height = this.height;
        
        // Update yScale range to use the new height
        this.yScale.range([this.height, 0]);
        
        // Set yScale domain to match the itemsHeight so x-axis is at bottom
        this.yScale.domain([0, itemsHeight]);
        
        // Update zoom background rectangle to cover full container
        if (this.app.zoomBackground) {
            const svgWidth = +this.svg.attr('width') || 0;
            this.app.zoomBackground
                .attr('width', svgWidth)
                .attr('height', this.height + this.margin.top + this.margin.bottom);
        }
        
        // Update clip paths to match new dimensions
        this.updateAxisClip();
        this.updateItemsClip();
        
        // Update axes
        const currentUnit = this.app.dimensionData.units.find(u => u.name === this.app.currentUnit);
        
        // Position x-axis at the bottom using yScale
        this.xAxis.attr('transform', `translate(0,${this.yScale(0)})`);
        
        // Position x-axis at the top
        this.xAxisTop.attr('transform', `translate(0,${this.yScale(itemsHeight)})`);
        
        // Generate ticks that are only powers of 10 (1eX format) for even spacing
        const tickValues = this.generateAxisTicks();

        this.xAxis.call(
            d3.axisBottom(this.xScale)
                .tickValues(tickValues)
                .tickFormat(d => this.app.formatAxisValue(d, 0))
        );
        // Extend axis domain lines to full container width
        const svgWidth = +this.svg.attr('width') || 0;
        const axisLeft = -this.margin.left;
        const axisRight = svgWidth - this.margin.left;
        this.xAxis.select('.domain')
            .attr('d', `M${axisLeft},0H${axisRight}`);
        
        // Post-process mathematical notation labels to use proper SVG superscripts
        if (this.app.notationMode === 'mathematical' && !this.app.usesLinearDisplayValues()) {
            this.app.processMathematicalLabels(this.xAxis);
        }
        
        this.xAxisTop.call(
            d3.axisTop(this.xScale)
                .tickValues(tickValues)
                .tickFormat(d => this.app.formatAxisValue(d, 0))
        );
        this.xAxisTop.select('.domain')
            .attr('d', `M${axisLeft},0H${axisRight}`);
        
        // Post-process mathematical notation labels to use proper SVG superscripts
        if (this.app.notationMode === 'mathematical' && !this.app.usesLinearDisplayValues()) {
            this.app.processMathematicalLabels(this.xAxisTop);
        }
        
        // Update grid
        this.updateGrid();
        
        // Draw items only (no bands for now)
        this.drawItems(positionedItems);
        
        // Create/update background rectangle for top axis after items are drawn
        // Append it after items so it's above items, then move axis after it so axis is on top
        if (!this.xAxisTopBackground) {
            this.xAxisTopBackground = this.mainGroup.append('rect')
                .attr('class', 'axis-top-background')
                .attr('x', -this.margin.left)
                .attr('y', 0)
                .attr('width', 0)
                .attr('height', 0)
                .style('pointer-events', 'none')
                .style('opacity', 0);
        }
        
        // Move top axis to be after background (so it renders on top)
        // This ensures rendering order: items < background < axis
        const topAxisNode = this.xAxisTop.node();
        const backgroundNode = this.xAxisTopBackground.node();
        if (topAxisNode.parentNode && backgroundNode.nextSibling !== topAxisNode) {
            topAxisNode.parentNode.insertBefore(topAxisNode, backgroundNode.nextSibling);
        }
        
        // Update sticky top axis after plot update
        if (this.app.updateStickyAxis) {
            this.app.updateStickyAxis();
        }
    }
    
    updatePlotAfterZoom() {
        // Ensure clip paths stay aligned with current dimensions
        this.updateAxisClip();
        this.updateItemsClip();
        
        // Generate ticks that are only powers of 10 (1eX format) for even spacing
        const tickValues = this.generateAxisTicks();
        
        // Get SVG dimensions for axis lines (SVG matches container)
        const svgWidth = +this.svg.attr('width') || 0;
        const axisLeft = -this.margin.left;
        const axisRight = svgWidth - this.margin.left;

        this.xAxis.call(
            d3.axisBottom(this.xScale)
                .tickValues(tickValues)
                .tickFormat(d => this.app.formatAxisValue(d, 0))
        );
        this.xAxis.select('.domain')
            .attr('d', `M${axisLeft},0H${axisRight}`);
        
        // Post-process mathematical notation labels to use proper SVG superscripts
        if (this.app.notationMode === 'mathematical' && !this.app.usesLinearDisplayValues()) {
            this.app.processMathematicalLabels(this.xAxis);
        }
        
        this.xAxisTop.call(
            d3.axisTop(this.xScale)
                .tickValues(tickValues)
                .tickFormat(d => this.app.formatAxisValue(d, 0))
        );
        this.xAxisTop.select('.domain')
            .attr('d', `M${axisLeft},0H${axisRight}`);
        
        // Post-process mathematical notation labels to use proper SVG superscripts
        if (this.app.notationMode === 'mathematical' && !this.app.usesLinearDisplayValues()) {
            this.app.processMathematicalLabels(this.xAxisTop);
        }
        
        // Update grid
        this.updateGrid();
        
        // Update vertical lines and item positions using existing layout data
        const yDomain = this.yScale.domain();
        const yTop = this.yScale(yDomain[1]);
        const yBottom = this.yScale(0);
        
        // Update item positions based on new scale
        // Use yScale to convert yPosition (which is in domain units) to screen coordinates
        // This ensures items stay in the same relative position even when height changes
        this.mainGroup.selectAll('.item-group')
            .attr('transform', d => {
                const x = this.xScale(d.convertedValue);
                // yPosition is stored as distance from bottom in domain units (0 to itemsHeight)
                // Use yScale to convert to screen coordinates, accounting for any height changes
                const y = this.yScale(d.yPosition);
                return `translate(${x},${y})`;
            });
        
        // Update vertical lines
        this.mainGroup.selectAll('.vertical-line')
            .attr('x1', d => this.xScale(d.convertedValue))
            .attr('x2', d => this.xScale(d.convertedValue))
            .attr('y1', yTop)
            .attr('y2', yBottom)
            .attr('stroke-opacity', CONFIG.VERTICAL_LINE_OPACITY);
        
        // Update label positions - labels should follow their points
        // The label x position is relative to the item-group transform, so it automatically follows
        // We just need to ensure it uses the correct offset
        this.mainGroup.selectAll('.item-label')
            .attr('x', CONFIG.LABEL_OFFSET_X);
        
        // Update sticky top axis after zoom update
        if (this.app.updateStickyAxis) {
            this.app.updateStickyAxis();
        }
    }
    
    updatePlotColors() {
        // Update colors based on current theme
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const colors = isDark ? CONFIG.COLORS.DARK : CONFIG.COLORS.LIGHT;
        const textColor = colors.TEXT;
        const axisColor = colors.AXIS;
        const strokeColor = colors.STROKE;
        const lineColor = colors.LINE;
        
        this.svg.selectAll('.axis text')
            .attr('fill', axisColor);
        
        this.svg.selectAll('.item-label')
            .attr('fill', textColor);
        
        // Update point stroke color
        this.svg.selectAll('.plot-item')
            .attr('stroke', strokeColor);
        
        // Update vertical line color
        this.svg.selectAll('.vertical-line')
            .attr('stroke', lineColor);
    }
}
