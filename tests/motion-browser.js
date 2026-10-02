// Run in the locally served site's browser console, or via agent-browser eval.
(async () => {
    const results = [];
    const check = (name, condition) => {
        if (!condition) throw new Error(name);
        results.push(name);
    };
    const tick = () =>
        new Promise((resolve) =>
            requestAnimationFrame(() => requestAnimationFrame(resolve))
        );
    const click = (view, label) => {
        const button = [...view.settings.querySelectorAll('button')].find(
            (node) => node.textContent === label
        );
        check(`${label}: control exists`, Boolean(button));
        button.click();
    };
    for (const dimension of [
        'speed',
        'acceleration',
        'jerk',
        'frequency',
        'sound-frequency',
        'angular-velocity'
    ]) {
        await app.setDimension(dimension);
        const view = app.experiences;
        view.setMode('interactive', false);
        for (const index of [
            0,
            Math.floor(view.items.length / 2),
            view.items.length - 1
        ]) {
            view.focus(index);
            await tick();
            check(
                `${dimension}/${index}: real-time default`,
                view.clock.rate === 1 && view.timeSlider.value === 0
            );
            const min = Number(view.timeSlider.input.min);
            const max = Number(view.timeSlider.input.max);
            check(
                `${dimension}/${index}: contextual bounds`,
                min <= 0 && max >= 0 && min > -55 && max < 20
            );
            for (const exponent of [min, 0, max]) {
                view.timeSlider.set(exponent);
                view.timeSlider.input.dispatchEvent(
                    new Event('input', { bubbles: true })
                );
                view.renderer.render(view.clock.rate * 2);
                check(
                    `${dimension}/${index}/${exponent}: finite geometry`,
                    !/NaN|Infinity/.test(
                        view.stage.innerHTML + view.live.textContent
                    )
                );
                check(
                    `${dimension}/${index}/${exponent}: finite positive clock`,
                    Number.isFinite(view.clock.rate) && view.clock.rate > 0
                );
            }
            click(view, 'Fit time to item');
            check(
                `${dimension}/${index}: fit is legible while paused`,
                !view.clock.playing &&
                    !/static diagram|Static timing diagram/.test(
                        view.stage.textContent
                    )
            );
            const seconds = ScaleMotionMath.duration(
                dimension,
                view.item.value
            );
            const expected = ScaleMotionMath.isLinear(dimension) ? 5 : 4;
            check(
                `${dimension}/${index}: fit crossing / period`,
                Math.abs(seconds / view.clock.rate - expected) <
                    expected * 0.012
            );
            click(view, 'Real time (1x)');
            check(
                `${dimension}/${index}: real-time reset`,
                view.clock.time === 0 && view.clock.rate === 1
            );
            check(
                `${dimension}/${index}: images retain aspect ratio`,
                [...view.stage.querySelectorAll('image')].every(
                    (image) =>
                        image.getAttribute('preserveAspectRatio') ===
                        'xMidYMid meet'
                )
            );
        }
        check(
            `${dimension}: explanatory notes exist`,
            view.caption.textContent.length > 100
        );
        view.playButton.click();
        await new Promise((resolve) => setTimeout(resolve, 120));
        check(
            `${dimension}: playback advances`,
            view.clock.playing && view.clock.time > 0
        );
        view.pause();
    }
    await app.setDimension('jerk');
    const view = app.experiences;
    view.setMode('interactive', false);
    view.focus(Math.floor(view.items.length / 2));
    view.renderer.render(1);
    check(
        'jerk: meaningful derivative feedback',
        /v .*m\/s.*a .*m\/s\^2/.test(view.live.textContent)
    );
    check(
        'jerk: equal-time markers',
        view.stage.querySelectorAll('.motion-time-sample').length ===
            view.pair.length * 5
    );
    check(
        'jerk: no spurious rotation',
        ![...view.stage.querySelectorAll('[transform]')].some((node) =>
            /rotate/.test(node.getAttribute('transform'))
        )
    );
    return { passed: results.length, results };
})();
