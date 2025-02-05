class GameEngine {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            throw new Error("Canvas not found: " + canvasId);
        }
        this.ctx = this.canvas.getContext('2d');
        this.lastUpdateTime = performance.now();
        this.running = false;
        this.gameLoop = this.gameLoop.bind(this);
    }

    start() {
        this.running = true;
        requestAnimationFrame(this.gameLoop);
    }

    stop() {
        this.running = false;
    }

    gameLoop(timestamp) {
        const dt = timestamp - this.lastUpdateTime;
        this.lastUpdateTime = timestamp;
        this.update(dt);
        this.render();
        if (this.running) {
            requestAnimationFrame(this.gameLoop);
        }
    }

    update(dt) {
        // Override this method in your game subclass
    }

    render() {
        // Override this method in your game subclass
    }
}

window.GameEngine = GameEngine;
