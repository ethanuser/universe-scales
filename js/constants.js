// Universal Scales - Constants Configuration

const CONFIG = {
    // Plot dimensions and margins
    MARGIN: { top: 24, right: 40, bottom: 20, left: 120 },
    MIN_SVG_HEIGHT: 200,
    
    // Item positioning
    FIXED_VERTICAL_SPACING: 14,
    BOTTOM_PADDING: 20,
    TOP_PADDING: 20,
    
    // Visual styling
    POINT_RADIUS: 6,
    POINT_RADIUS_HOVER: 8,
    POINT_STROKE_WIDTH: 1.5,
    POINT_STROKE_WIDTH_HOVER: 3,
    POINT_FILL_COLOR: '#007bff',
    POINT_STROKE_COLOR: '#000000',
    
    // Vertical lines
    VERTICAL_LINE_STROKE_WIDTH: 1,
    VERTICAL_LINE_OPACITY: 0.2,
    VERTICAL_LINE_DASH_ARRAY: '3,3',
    
    // Text labels
    LABEL_FONT_SIZE: '9px',
    LABEL_OFFSET_X: -10,
    LABEL_OFFSET_Y: -12,
    LABEL_HEIGHT: 24,
    LABEL_PADDING: 20,
    LABEL_CIRCLE_PADDING: 10,
    TEXT_WIDTH_ESTIMATE: 6, // pixels per character
    
    // Horizontal positioning
    TEXT_BUFFER: 5,
    
    // Tooltip positioning
    TOOLTIP_OFFSET_X: 10,
    TOOLTIP_OFFSET_Y: 10,
    TOOLTIP_MIN_TOP: 10,
    TOOLTIP_MIN_WIDTH: 160,
    TOOLTIP_MAX_WIDTH: 400,
    TOOLTIP_VIEWPORT_BOTTOM_MARGIN: 12,
    
    // Animation
    HOVER_TRANSITION_DURATION: 100,
    RESET_ZOOM_TRANSITION_DURATION: 750,
    RESIZE_DEBOUNCE_MS: 150, // Debounce delay for window resize events
    
    // Grid
    GRID_TICKS: 10,
    AXIS_TICKS: 10,
    CANDIDATE_TICKS_COUNT: 50,
    
    // Number formatting
    VALUE_FORMAT: '.2e',
    AXIS_FORMAT: '.0e',
    
    // Debug threshold
    DEBUG_SMALL_VALUE_THRESHOLD: 1e-10,
    
    // Zoom behavior
    ZOOM_SCALE_MIN: 0.1,
    ZOOM_SCALE_MAX: 100,
    // Allow generous horizontal overscroll so zoom/pan can reach both min and max items,
    // even on narrow mobile portrait at high zoom levels. Domain clamping in handleZoom
    // still ensures we never see beyond the actual item extent.
    ZOOM_TRANSLATE_PADDING_RATIO: 10,
    
    // Domain extent
    EXTENT_LOWER_MULTIPLIER: 0.1, // Extend lower bound for text label space
    EXTENT_UPPER_MULTIPLIER: 1e1, // Extend upper bound for domain
    LINEAR_EXTENT_PADDING_RATIO: 0.08, // Padding for linear-scale domains
    
    // Tick generation thresholds
    TICK_ZOOM_LEVEL_CHANGE_THRESHOLD: 0.15, // 15% change in range (lower for more responsive tick updates)
    TICK_DOMAIN_SHIFT_THRESHOLD: 0.8, // 80% of current range
    TICK_EXPANDED_RANGE_BUFFER: 0.3, // Buffer for stability in log space
    TICK_MIN_COUNT: 2, // Minimum number of ticks to show
    
    // Domain change detection
    DOMAIN_CHANGE_THRESHOLD: 0.1, // 10% change to trigger reset
    ZOOM_DETECTION_THRESHOLD: 0.01, // 1% change to detect zoom state
    
    // Label spacing
    LABEL_SPACING_MOBILE: 56, // pixels between labels on mobile
    LABEL_SPACING_DESKTOP: 72, // pixels between labels on desktop
    MOBILE_BREAKPOINT: 480, // pixels
    
    // Touch target
    TAP_TARGET_RADIUS: 24, // larger hit area for fingers
    LABEL_HEIGHT_MOBILE_MIN: 32, // minimum label height on mobile
    LABEL_OFFSET_Y_MOBILE_ADJUSTMENT: -6, // vertical adjustment on mobile
    MAX_CLICK_DISTANCE: 5, // pixels - maximum movement to register as click (not drag)
    
    // Event handling
    PARENT_CHECK_DEPTH: 5, // Maximum depth to check parent elements for event filtering
    VERTICAL_SCROLL_THRESHOLD: 1, // pixels - minimum vertical movement to trigger page scroll
    
    // Mathematical constants
    LOG_BASE: 10, // Base for logarithmic calculations
    
    // Colors
    COLORS: {
        LIGHT: {
            TEXT: '#212529',
            AXIS: '#6c757d',
            STROKE: '#000000',
            LINE: '#007bff'
        },
        DARK: {
            TEXT: '#ffffff',
            AXIS: '#adb5bd',
            STROKE: '#ffffff',
            LINE: '#4dabf7'
        }
    },
    
    // Notation toggle button texts
    NOTATION_BUTTON_TEXTS: {
        'scientific': '1e10',
        'mathematical': '1×10^10',
        'human': '10B',
        'si': '10 km'
    }
};
