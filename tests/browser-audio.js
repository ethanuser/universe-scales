(async () => {
    const checks = [];
    const check = (name, condition) => {
        if (!condition) throw new Error(name);
        checks.push(name);
    };
    await app.setDimension('sound-intensity');
    const audio = app.experiences.audio;
    await audio.ready;
    // Run after one real Play click so the browser has granted audio activation.
    for (const name of Object.keys(audio.clips)) {
        const item = app.getAllItems().find((i) => i.name === name);
        check(`${name}: dataset match`, !!item);
        app.showTooltip({ clientX: 200, clientY: 200 }, item, true);
        await audio.ready;
        const play = app.tooltip.querySelector('.experience-audio button');
        const status = app.tooltip.querySelector('.experience-audio [role=status]');
        await audio.play(item, play, status);
        check(`${name}: decoded real recording`, !!audio.node?.buffer);
        check(`${name}: music paused`, app.backgroundMusic.paused);
        app.hideTooltip();
        check(`${name}: stops on close`, !audio.node);
    }
    const missing = app.getAllItems().find((i) => !audio.clips[i.name]);
    app.showTooltip({ clientX: 200, clientY: 200 }, missing, true);
    await audio.ready;
    check('missing recording disabled', app.tooltip.querySelector('.experience-audio button').disabled);
    const rain = app.getAllItems().find((i) => i.name === 'Rainfall');
    app.showTooltip({ clientX: 200, clientY: 200 }, rain, true);
    await audio.ready;
    const play = app.tooltip.querySelector('.experience-audio button');
    const status = app.tooltip.querySelector('.experience-audio [role=status]');
    await audio.play(rain, play, status, true);
    check('reference is playable at fixed level', !!audio.node && audio.referencePlayed);
    audio.stop();
    audio.referenceDb = 65;
    await audio.play(rain, play, status);
    check('calibration applied', status.textContent.includes('50.0 dB SPL'));
    audio.stop(); audio.referenceDb = null;
    const pending = audio.play(rain, play, status);
    audio.stop(); await pending;
    check('cancelled playback cannot restart', !audio.node);
    app.hideTooltip();
    return { passed: checks.length, checks };
})()
