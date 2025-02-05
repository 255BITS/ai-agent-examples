class BreakoutGame extends GameEngine {
  constructor(canvasId) {
    super(canvasId);
    this.canvasWidth = this.canvas.width;
    this.canvasHeight = this.canvas.height;

    // Paddle configuration
    this.paddle = {
      width: 75,
      height: 10,
      x: (this.canvasWidth - 75) / 2,
      y: this.canvasHeight - 20,
      speed: 300 // pixels per second
    };

    // Ball configuration
    this.ball = {
      x: this.canvasWidth / 2,
      y: this.canvasHeight - 30,
      radius: 10,
      speed: 250,  // used for scaling dx based on impact
      dx: 150,     // initial horizontal velocity (px/sec)
      dy: -150     // initial vertical velocity (px/sec)
    };

    // Bricks configuration
    this.brickConfig = {
      rowCount: 3,
      colCount: 5,
      width: 75,
      height: 20,
      padding: 10,
      offsetTop: 30,
      offsetLeft: 30
    };
    this.bricks = [];
    for (let r = 0; r < this.brickConfig.rowCount; r++) {
      this.bricks[r] = [];
      for (let c = 0; c < this.brickConfig.colCount; c++) {
        const brickX = c * (this.brickConfig.width + this.brickConfig.padding) + this.brickConfig.offsetLeft;
        const brickY = r * (this.brickConfig.height + this.brickConfig.padding) + this.brickConfig.offsetTop;
        this.bricks[r][c] = { x: brickX, y: brickY, status: 1 };
      }
    }

    // Input handling for paddle movement
    this.rightPressed = false;
    this.leftPressed = false;
    document.addEventListener("keydown", (e) => this.keyDownHandler(e), false);
    document.addEventListener("keyup", (e) => this.keyUpHandler(e), false);
  }

  keyDownHandler(e) {
    if (e.key === "Right" || e.key === "ArrowRight") {
      this.rightPressed = true;
    } else if (e.key === "Left" || e.key === "ArrowLeft") {
      this.leftPressed = true;
    }
  }

  keyUpHandler(e) {
    if (e.key === "Right" || e.key === "ArrowRight") {
      this.rightPressed = false;
    } else if (e.key === "Left" || e.key === "ArrowLeft") {
      this.leftPressed = false;
    }
  }

  update(dt) {
    // Convert dt (ms) to seconds.
    const delta = dt / 1000;

    // --- Update Paddle Position ---
    if (this.rightPressed) {
      this.paddle.x += this.paddle.speed * delta;
      if (this.paddle.x + this.paddle.width > this.canvasWidth) {
        this.paddle.x = this.canvasWidth - this.paddle.width;
      }
    }
    if (this.leftPressed) {
      this.paddle.x -= this.paddle.speed * delta;
      if (this.paddle.x < 0) {
        this.paddle.x = 0;
      }
    }

    // --- Update Ball Position ---
    this.ball.x += this.ball.dx * delta;
    this.ball.y += this.ball.dy * delta;

    // --- Ball-Wall Collisions ---
    // Left and right walls.
    if (this.ball.x + this.ball.radius > this.canvasWidth || this.ball.x - this.ball.radius < 0) {
      this.ball.dx = -this.ball.dx;
    }
    // Top wall.
    if (this.ball.y - this.ball.radius < 0) {
      this.ball.dy = -this.ball.dy;
    }
    // Bottom wall: end game.
    if (this.ball.y + this.ball.radius > this.canvasHeight) {
      alert("GAME OVER");
      document.location.reload();
      this.stop();
    }

    // --- Ball-Paddle Collision ---
    if (
      this.ball.x > this.paddle.x &&
      this.ball.x < this.paddle.x + this.paddle.width &&
      this.ball.y + this.ball.radius > this.paddle.y &&
      this.ball.y - this.ball.radius < this.paddle.y + this.paddle.height
    ) {
      this.ball.dy = -this.ball.dy;
      // Adjust horizontal speed based on hit location.
      let hitPoint = this.ball.x - (this.paddle.x + this.paddle.width / 2);
      hitPoint = hitPoint / (this.paddle.width / 2); // Normalize between -1 and 1.
      this.ball.dx = hitPoint * this.ball.speed;
    }

    // --- Ball-Brick Collisions ---
    for (let r = 0; r < this.brickConfig.rowCount; r++) {
      for (let c = 0; c < this.brickConfig.colCount; c++) {
        const brick = this.bricks[r][c];
        if (brick.status === 1) {
          if (
            this.ball.x > brick.x &&
            this.ball.x < brick.x + this.brickConfig.width &&
            this.ball.y - this.ball.radius < brick.y + this.brickConfig.height &&
            this.ball.y + this.ball.radius > brick.y
          ) {
            this.ball.dy = -this.ball.dy;
            brick.status = 0;
          }
        }
      }
    }
  }

  render() {
    // Clear the canvas.
    this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);

    // --- Draw Ball ---
    this.ctx.beginPath();
    this.ctx.arc(this.ball.x, this.ball.y, this.ball.radius, 0, Math.PI * 2);
    this.ctx.fillStyle = "#0095DD";
    this.ctx.fill();
    this.ctx.closePath();

    // --- Draw Paddle ---
    this.ctx.beginPath();
    this.ctx.rect(this.paddle.x, this.paddle.y, this.paddle.width, this.paddle.height);
    this.ctx.fillStyle = "#0095DD";
    this.ctx.fill();
    this.ctx.closePath();

    // --- Draw Bricks ---
    for (let r = 0; r < this.brickConfig.rowCount; r++) {
      for (let c = 0; c < this.brickConfig.colCount; c++) {
        const brick = this.bricks[r][c];
        if (brick.status === 1) {
          this.ctx.beginPath();
          this.ctx.rect(brick.x, brick.y, this.brickConfig.width, this.brickConfig.height);
          this.ctx.fillStyle = "#0095DD";
          this.ctx.fill();
          this.ctx.closePath();
        }
      }
    }
  }
}

// Instantiate and start the game once the window is loaded.
window.onload = function() {
  const breakoutGame = new BreakoutGame("gameCanvas");
  breakoutGame.start();
};
