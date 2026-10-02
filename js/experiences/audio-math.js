(function (root) {
    const referenceRms = 0.008;
    const attenuationGain = (db) => {
        if (!Number.isFinite(db) || db < -40 || db > 0) throw new Error('Invalid attenuation');
        return 10 ** (db / 20);
    };
    function playbackLevel(rms, peak, targetDb, referenceDb = 70, calibrated = false, attenuationDb = 0) {
        if (!(rms > 0) || !(peak > 0) || ![rms, peak, targetDb, referenceDb].every(Number.isFinite))
            throw new Error('Invalid recording level');
        const desiredRms = referenceRms * 10 ** ((targetDb - referenceDb) / 20);
        const ceiling = Math.min(referenceRms, calibrated
            ? referenceRms * 10 ** ((75 - referenceDb) / 20) : referenceRms);
        const baseGain = Math.min(desiredRms / rms, ceiling / rms, 0.18 / peak);
        // Attenuate after limiting so even a capped rocket preview gets quieter.
        const gain = baseGain * attenuationGain(attenuationDb);
        return {
            gain,
            limited: baseGain < desiredRms / rms * 0.999,
            relativeDb: 20 * Math.log10(gain * rms / referenceRms),
            // A model value for API compatibility, never a measurement of device output.
            estimatedDb: referenceDb + 20 * Math.log10(gain * rms / referenceRms)
        };
    }
    function digitalLevel(samples) {
        let energy = 0;
        for (const sample of samples) {
            if (!Number.isFinite(sample)) return -96;
            energy += sample * sample;
        }
        return energy > 0 ? Math.max(-96, Math.min(0, 10 * Math.log10(energy / samples.length))) : -96;
    }
    const api = { playbackLevel, referenceRms, attenuationGain, digitalLevel };
    if (typeof module !== 'undefined') module.exports = api;
    root.ScaleAudioMath = api;
})(globalThis);
