// Universal Scales - Number Formatting Utilities

class NumberFormatter {
    static SI_PREFIXES = [
        { exponent: 24, symbol: 'Y' }, { exponent: 21, symbol: 'Z' },
        { exponent: 18, symbol: 'E' }, { exponent: 15, symbol: 'P' },
        { exponent: 12, symbol: 'T' }, { exponent: 9, symbol: 'G' },
        { exponent: 6, symbol: 'M' }, { exponent: 3, symbol: 'k' },
        { exponent: 0, symbol: '' }, { exponent: -3, symbol: 'm' },
        { exponent: -6, symbol: 'μ' }, { exponent: -9, symbol: 'n' },
        { exponent: -12, symbol: 'p' }, { exponent: -15, symbol: 'f' },
        { exponent: -18, symbol: 'a' }, { exponent: -21, symbol: 'z' },
        { exponent: -24, symbol: 'y' }
    ];

    constructor(notationMode) {
        this.notationMode = notationMode;
    }
    
    setNotationMode(mode) {
        this.notationMode = mode;
    }
    
    formatNumber(value, precision = 0, forTooltip = false) {
        if (value === 0) return '0';
        
        const absValue = Math.abs(value);
        const sign = value < 0 ? '-' : '';
        
        switch (this.notationMode) {
            case 'scientific':
                // Use d3 format for scientific notation
                return d3.format(`.${precision}e`)(value);
            
            case 'mathematical':
                // Format as 1×10^10 or 1×10⁻¹⁰
                const exponent = Math.floor(Math.log10(absValue));
                const mantissa = absValue / Math.pow(10, exponent);
                
                // Round mantissa to appropriate precision
                const roundedMantissa = Math.round(mantissa * Math.pow(10, precision)) / Math.pow(10, precision);
                
                if (forTooltip) {
                    // For tooltips and buttons, return HTML with superscripts
                    return this.formatMathematicalHTML(sign, roundedMantissa, exponent);
                } else {
                    // For axes, return a special format that we'll process into SVG tspan elements
                    // Format: "mantissa×10|exponent" where | is a delimiter
                    return `${sign}${roundedMantissa}×10|${exponent}`;
                }
            
            case 'human':
                // Format as human-readable numbers (billion, million, etc.)
                return this.formatHumanReadable(value, precision);

            case 'si':
                return this.formatSINumber(value, precision);
            
            default:
                return d3.format(`.${precision}e`)(value);
        }
    }

    formatSIValue(value, unitSymbol = '', precision = 2) {
        const symbol = String(unitSymbol || '');
        if (!symbol || !Number.isFinite(Number(value)) || Number(value) === 0) {
            return `${this.formatSINumber(value, precision)}${symbol ? ` ${this.formatDisplayUnitSymbol(symbol)}` : ''}`;
        }

        // A prefix on a compound expression multiplies that entire expression.
        // In particular, k(kg/m^3) must not be mistaken for kg/(km)^3.
        if (/[/*·]/.test(symbol)) return this.formatSIExpression(value, symbol, precision);
        const parsed = this.parsePrefixedUnit(symbol);
        const unit = parsed || { prefixExponent: 0, baseSymbol: symbol, power: 1 };
        const valueInBase = Number(value) * (10 ** (unit.prefixExponent * unit.power));
        const step = 3 * unit.power;
        const rawExponent = Math.floor(Math.log10(Math.abs(valueInBase)) / step) * 3;
        const boundedExponent = Math.max(-24, Math.min(24, rawExponent));
        const prefix = NumberFormatter.SI_PREFIXES.find(entry => entry.exponent === boundedExponent);
        let scaled = valueInBase / (10 ** (boundedExponent * unit.power));
        let formatted = this.formatSIScaled(scaled, precision);

        // Carry rounded 1000 into the next prefix when one exists.
        if (Math.abs(Number(formatted)) >= 1000 && boundedExponent < 24) {
            const nextExponent = boundedExponent + 3;
            const nextPrefix = NumberFormatter.SI_PREFIXES.find(entry => entry.exponent === nextExponent);
            if (nextPrefix) {
                scaled /= 10 ** (3 * unit.power);
                formatted = this.formatSIScaled(scaled, precision);
                if (Math.abs(Number(formatted)) >= 1 && Math.abs(Number(formatted)) < 1000) {
                    return `${formatted} ${this.formatDisplayUnitSymbol(`${nextPrefix.symbol}${unit.baseSymbol}`)}`;
                }
            }
        }

        const isOutOfRange = rawExponent > 24 || rawExponent < -24;
        if (isOutOfRange) {
            const scientificExponent = Math.floor(Math.log10(Math.abs(scaled)));
            const mantissa = scaled / (10 ** scientificExponent);
            const sci = `${this.formatSIScaled(mantissa, precision)}e${scientificExponent}`;
            return `${sci} ${this.formatDisplayUnitSymbol(`${prefix.symbol}${unit.baseSymbol}`)}`;
        }
        if (Math.abs(Number(formatted)) < 1 || Math.abs(Number(formatted)) >= 1000) {
            // Centi/deci/deca/hecto also give useful conventional powered units.
            for (const [exponent, smallPrefix] of [[2, 'h'], [1, 'da'], [-1, 'd'], [-2, 'c']]) {
                const candidate = this.formatSIScaled(valueInBase / 10 ** (exponent * unit.power), precision);
                if (Math.abs(Number(candidate)) >= 1 && Math.abs(Number(candidate)) < 1000)
                    return `${candidate} ${this.formatDisplayUnitSymbol(`${smallPrefix}${unit.baseSymbol}`)}`;
            }
            return this.formatSIExpression(value, symbol, precision);
        }
        return `${formatted} ${this.formatDisplayUnitSymbol(`${prefix.symbol}${unit.baseSymbol}`)}`;
    }

    formatScientific(value, precision) {
        const [mantissa, exponent] = Number(value).toExponential(this.siSignificantDigits(precision) - 1).split('e');
        return `${Number(mantissa)}e${exponent}`;
    }

    formatDisplayUnitSymbol(symbol) {
        return String(symbol).replace(/\^(?:2\b|\{2\})/g, '²').replace(/\^(?:3\b|\{3\})/g, '³');
    }

    formatSINumber(value, precision = 2) {
        const number = Number(value);
        if (!Number.isFinite(number) || number === 0) return String(number);
        const exponent = Math.floor(Math.log10(Math.abs(number)) / 3) * 3;
        const prefix = NumberFormatter.SI_PREFIXES.find(entry => entry.exponent === Math.max(-24, Math.min(24, exponent)));
        const scaled = number / (10 ** prefix.exponent);
        const formatted = this.formatSIScaled(scaled, precision);
        if (exponent > 24 || exponent < -24) {
            return `${this.formatScientific(scaled, precision)}${prefix.symbol}`;
        }
        if (Math.abs(Number(formatted)) >= 1000 && prefix.exponent < 24) {
            const next = NumberFormatter.SI_PREFIXES.find(entry => entry.exponent === prefix.exponent + 3);
            if (next) return `${this.formatSIScaled(scaled / 1000, precision)}${next.symbol}`;
        }
        return `${formatted}${prefix.symbol}`;
    }

    formatSIExpression(value, symbol, precision) {
        const text = this.formatSINumber(value, precision);
        const prefix = NumberFormatter.SI_PREFIXES.find(entry => entry.symbol && text.endsWith(entry.symbol));
        if (!prefix) return `${text} ${this.formatDisplayUnitSymbol(symbol)}`;
        return `${text.slice(0, -prefix.symbol.length)} ${prefix.symbol}(${this.formatDisplayUnitSymbol(symbol)})`;
    }

    siSignificantDigits(precision) {
        return Math.min(3, Math.max(1, (Number(precision) || 0) + 1));
    }

    formatSIScaled(value, precision) {
        return String(Number(Number(value).toPrecision(this.siSignificantDigits(precision))));
    }

    formatFixed(value, precision) {
        const digits = Math.max(0, Math.min(12, Number(precision) || 0));
        return Number(value).toFixed(digits).replace(/(\.\d*?[1-9])0+$|\.0+$/, '$1') || '0';
    }

    parsePrefixedUnit(symbol) {
        const match = String(symbol).match(/(?:\^\{([23])\}|\^([23])|([²³]))$/);
        const power = match ? Number((match[1] || match[2] || match[3]).replace('²', '2').replace('³', '3')) : 1;
        const expression = match ? symbol.slice(0, -match[0].length) : symbol;
        const prefixes = [
            ...NumberFormatter.SI_PREFIXES.filter(entry => entry.symbol),
            { exponent: -2, symbol: 'c' }, { exponent: -1, symbol: 'd' },
            { exponent: 1, symbol: 'da' }, { exponent: 2, symbol: 'h' }
        ].sort((a, b) => b.symbol.length - a.symbol.length);
        const prefixedBases = new Set(['m', 's', 'g', 'A', 'K', 'mol', 'cd', 'Hz', 'N', 'Pa', 'J', 'W', 'C', 'V', 'F', 'Ω', 'S', 'Wb', 'T', 'H', 'lm', 'lx', 'B', 'L', 'Wh']);
        for (const entry of prefixes) {
            const baseSymbol = expression.slice(entry.symbol.length);
            if (prefixedBases.has(baseSymbol) && expression.startsWith(entry.symbol)) {
                return {
                    prefixExponent: entry.exponent,
                    baseSymbol: `${baseSymbol}${match ? match[0] : ''}`,
                    power
                };
            }
        }
        return match ? { prefixExponent: 0, baseSymbol: symbol, power } : null;
    }

    formatLinearNumber(value, precision = 2) {
        if (value === 0) return '0';

        const absValue = Math.abs(value);
        let digits = precision;
        if (absValue < 0.01) {
            digits = Math.max(4, precision + 2);
        } else if (absValue < 1) {
            digits = Math.max(3, precision + 1);
        } else if (absValue >= 100) {
            digits = 0;
        }

        const formatted = d3.format(`,.${digits}f`)(value)
            .replace(/(\.\d*?[1-9])0+$/, '$1')
            .replace(/\.0+$/, '');
        return formatted === '-0' ? '0' : formatted;
    }
    
    formatMathematicalHTML(sign, mantissa, exponent) {
        // Format as HTML with superscript: 1×10<sup>-22</sup>
        const exponentStr = exponent.toString();
        return `${sign}${mantissa}×10<sup>${exponentStr}</sup>`;
    }
    
    formatHumanReadable(value, precision = 2) {
        if (value === 0) return '0';
        
        const absValue = Math.abs(value);
        const sign = value < 0 ? '-' : '';
        
        // For very small numbers (< 0.001), use scientific notation format (e.g., 1.5e-10)
        if (absValue < 0.001 && absValue > 0) {
            return d3.format(`.${precision}e`)(value);
        }
        
        // For very large numbers (> 1e15), use scientific notation format (e.g., 1.5e15)
        if (absValue >= 1e15) {
            return d3.format(`.${precision}e`)(value);
        }
        
        // Define thresholds and labels for human-readable format
        const units = [
            { value: 1e12, label: 'T' }, // Trillion
            { value: 1e9, label: 'B' },  // Billion
            { value: 1e6, label: 'M' },   // Million
            { value: 1e3, label: 'K' },  // Thousand
            { value: 1, label: '' }
        ];
        
        // Find appropriate unit
        let unit = units[units.length - 1];
        for (let i = 0; i < units.length; i++) {
            if (absValue >= units[i].value) {
                unit = units[i];
                break;
            }
        }
        
        // Format with unit
        const scaledValue = absValue / unit.value;
        const roundedValue = Math.round(scaledValue * Math.pow(10, precision)) / Math.pow(10, precision);
        
        // Remove trailing zeros, but keep at least one digit after decimal if precision > 0
        let formatted;
        if (precision > 0) {
            formatted = roundedValue.toFixed(precision).replace(/\.?0+$/, '');
            // Ensure at least one decimal place for values < 1
            if (absValue < 1 && !formatted.includes('.')) {
                formatted = roundedValue.toFixed(1);
            }
        } else {
            formatted = Math.round(scaledValue).toString();
        }
        
        return `${sign}${formatted}${unit.label}`;
    }
    
    processMathematicalLabels(axis) {
        // Process all text elements in the axis to convert mathematical notation
        // from "mantissa×10|exponent" format to proper SVG with tspan superscripts
        axis.selectAll('text').each(function() {
            const textElement = d3.select(this);
            const originalText = textElement.text();
            
            // Check if this is a mathematical notation label (contains "|")
            if (originalText.includes('|')) {
                const parts = originalText.split('|');
                if (parts.length === 2) {
                    const base = parts[0];
                    const exponent = parts[1];
                    
                    // Clear the text content
                    textElement.text('');
                    
                    // Add the base text
                    textElement.append('tspan')
                        .text(base);
                    
                    // Add the exponent as a superscript tspan
                    const isNegative = exponent.startsWith('-');
                    const expValue = isNegative ? exponent.substring(1) : exponent;
                    
                    // Combine negative sign and exponent digits in one tspan for proper alignment
                    const exponentText = isNegative ? `-${expValue}` : expValue;
                    textElement.append('tspan')
                        .attr('baseline-shift', 'super')
                        .attr('font-size', '0.7em')
                        .text(exponentText);
                }
            }
        });
    }
}
