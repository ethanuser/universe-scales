const { test } = require('node:test');
const assert = require('node:assert/strict');
const M = require('../js/experiences/motion-math.js');
const close = (actual, expected, tolerance = 1e-10) =>
    assert.ok(
        Math.abs(actual - expected) <=
            tolerance * Math.max(Math.abs(expected), 1e-280),
        `${actual} != ${expected}`
    );

test('speed, acceleration, and jerk integrate from explicit initial conditions', () => {
    for (const [dimension, expected] of [
        ['speed', [6, 3, 0, 0]],
        ['acceleration', [6, 6, 3, 0]],
        ['jerk', [4, 6, 6, 3]]
    ]) {
        Object.values(M.kinematics(dimension, 3, 2)).forEach((value, i) =>
            close(value, expected[i])
        );
    }
    assert.deepEqual(M.kinematics('speed', 3, 0), {
        position: 0,
        velocity: 3,
        acceleration: 0,
        jerk: 0
    });
    assert.deepEqual(M.kinematics('acceleration', 3, 0), {
        position: 0,
        velocity: 0,
        acceleration: 3,
        jerk: 0
    });
    assert.deepEqual(M.kinematics('jerk', 3, 0), {
        position: 0,
        velocity: 0,
        acceleration: 0,
        jerk: 3
    });
});

test('analytic velocity, acceleration, and jerk agree with numerical derivatives', () => {
    const dt = 1e-4;
    for (const dimension of ['speed', 'acceleration', 'jerk']) {
        const left = M.kinematics(dimension, 7, 2 - dt);
        const right = M.kinematics(dimension, 7, 2 + dt);
        const at = M.kinematics(dimension, 7, 2);
        for (const [integral, derivative] of [
            ['position', 'velocity'],
            ['velocity', 'acceleration'],
            ['acceleration', 'jerk']
        ])
            close(
                (right[integral] - left[integral]) / (2 * dt),
                at[derivative],
                1e-8
            );
    }
});

test('crossing times invert position over very large and very small scales', () => {
    for (const dimension of ['speed', 'acceleration', 'jerk']) {
        for (const value of [1e-250, 1e-10, 1, 9.81, 1e30, 1e250]) {
            for (const distance of [1e-6, 100, 1e12]) {
                const time = M.duration(dimension, value, distance);
                assert.ok(Number.isFinite(time) && time > 0);
                close(M.kinematics(dimension, value, time).position, distance);
            }
        }
    }
    close(M.kinematics('jerk', 1e-250, 1e150).position, 1e200 / 6);
    close(M.kinematics('jerk', 1e250, 1e-150).position, 1e-200 / 6);
});

test('angular velocity uses radians, with 2 pi radians in a full turn', () => {
    close(M.duration('angular-velocity', 2 * Math.PI), 1);
    const state = M.cycleState('angular-velocity', 2 * Math.PI, 0.25);
    close(state.hz, 1);
    close(state.phase, Math.PI / 2);
    close(M.duration('frequency', 440), 1 / 440);
    close(M.duration('sound-frequency', 440), 1 / 440);
});

test('bounds are contextual, finite, strictly positive rates and include exactly 1x', () => {
    for (const dimension of [
        'speed',
        'acceleration',
        'jerk',
        'frequency',
        'sound-frequency',
        'angular-velocity'
    ]) {
        for (const value of [2.285e-18, 1e-9, 1, 440, 1e20, 1e300]) {
            const bounds = M.timeBounds(dimension, value);
            assert.ok(bounds.min <= 0 && bounds.max >= 0);
            assert.ok(bounds.min < bounds.max);
            assert.ok(bounds.fit >= bounds.min && bounds.fit <= bounds.max);
            for (const exponent of Object.values(bounds)) {
                assert.ok(
                    Number.isFinite(10 ** exponent) && 10 ** exponent > 0
                );
            }
            if (Math.abs(bounds.fit) < 300) {
                close(
                    M.duration(dimension, value) / 10 ** bounds.fit,
                    M.isLinear(dimension) ? 5 : 4
                );
            }
        }
    }
    const walking = M.timeBounds('speed', 20);
    assert.equal(walking.min, -1);
    assert.equal(walking.max, 1);
    assert.ok(Math.abs(walking.fit) < 1e-12);
    assert.ok(M.timeBounds('frequency', 440).min > -10);
    assert.ok(M.timeBounds('frequency', 440).max < 2);
    assert.notDeepEqual(
        M.timeBounds('speed', 20, 100),
        M.timeBounds('speed', 20, 1.7)
    );
});

test('fast cycles freeze explicitly and fitting restores the recorded period', () => {
    const real = M.cycleState('sound-frequency', 440, 1234);
    assert.ok(real.unresolved);
    assert.equal(real.phase, 0);
    const fit = M.timeBounds('sound-frequency', 440).fit;
    const slow = M.cycleState('sound-frequency', 440, 1 / (440 * 4), 10 ** fit);
    assert.equal(slow.unresolved, false);
    close(slow.visibleHz, 0.25);
    close(slow.phase, Math.PI / 2);
    close(slow.hz, 440);
    assert.equal(M.cycleState('frequency', 8, 0.1).unresolved, false);
    assert.equal(M.cycleState('frequency', 8.01, 0.1).unresolved, true);
});

test('only actual rotation and orbit examples use rotary visuals', () => {
    assert.equal(
        M.visualKind('acceleration', "Earth's Rotation at Equator"),
        'linear'
    );
    assert.equal(M.visualKind('jerk', 'Robot Arm Motion'), 'linear');
    assert.equal(M.visualKind('speed', 'Earth orbit'), 'linear');
    assert.equal(
        M.visualKind('angular-velocity', 'Earth orbit around the Sun'),
        'orbit'
    );
    assert.equal(M.visualKind('angular-velocity', 'Ceiling fan'), 'spin');
    assert.equal(M.visualKind('frequency', 'Galactic year'), 'orbit');
    assert.equal(M.visualKind('frequency', 'Minute hand revolution'), 'spin');
    assert.equal(M.visualKind('frequency', 'Ceiling fan on high'), 'spin');
    assert.equal(M.visualKind('frequency', 'Resting heartbeat'), 'pulse');
    assert.equal(M.visualKind('frequency', 'Resting breathing'), 'pulse');
    assert.equal(
        M.visualKind('frequency', 'Hummingbird wingbeat'),
        'oscillation'
    );
    assert.equal(
        M.visualKind('sound-frequency', 'Mosquito wingbeat'),
        'oscillation'
    );
    assert.equal(M.visualKind('sound-frequency', 'Ceiling fan'), 'oscillation');
});

test('invalid linear model inputs are rejected', () => {
    assert.throws(() => M.kinematics('angular-velocity', 1, 1), RangeError);
    assert.throws(() => M.kinematics('jerk', -1, 1), RangeError);
    assert.throws(() => M.kinematics('jerk', 1, -1), RangeError);
    assert.throws(() => M.kinematics('jerk', NaN, 1), RangeError);
    assert.throws(() => M.duration('speed', 0), RangeError);
    assert.throws(() => M.duration('speed', 1, Infinity), RangeError);
});
