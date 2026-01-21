from actifix.raise_af import record_error, TicketPriority

tickets_data = [
    {
        'source': 'shootymcshoot:missing_main_menu',
        'message': 'Missing main menu system for ShootyMcShoot R-Type style game. The current module only serves a placeholder React page. Need full main menu with: - Title screen with \\"ShootyMcShoot\\" branding in R-Type style (bold sci-fi font, space background). - \\"Start Game\\" button transitioning to level 1. - \\"Exit Game\\" button closing or returning to menu. - Smooth fade/transition animations. - Keyboard navigation (Enter to select, ESC to back). - Responsive design for 900x600 browser viewport. - Game state manager enum: MENU, PLAYING, PAUSED, GAME_OVER, VICTORY, BOSS. Implement using vanilla JS state machine in Canvas context. Ensure integration with existing Flask blueprint /health endpoint remains functional. After implementation, test menu responsiveness and transitions.',
        'error_type': 'FeatureMissing'
    },
    {
        'source': 'shootymcshoot:missing_game_engine',
        'message': 'Missing core game engine for ShootyMcShoot. Require: - Full HTML5 Canvas setup (900x600 viewport). - RAF-based game loop with deltaTime for smooth 60FPS. - Entity base class with update/render methods. - QuadTree or simple collision detection (AABB). - Scrolling starfield background (parallax layers). - Input handler for keyboard events (WASD/Arrows move, Space shoot, ESC pause). - Audio context hooks for SFX (explosions, shoot, optional). - Particle system base for explosions/smoke. All pure vanilla JS, no libs. Replace current _HTML_PAGE placeholder. Ensure ModuleBase error handling wraps game init.',
        'error_type': 'FeatureMissing'
    },
    {
        'source': 'shootymcshoot:missing_player_ship',
        'message': 'Missing player ship implementation. Features: - Ship entity: position, velocity, sprite (🚀 emoji or Canvas path). - Movement: clamped to screen bounds, acceleration/friction physics. - Controls: WASD/Arrows thrust/turn, auto-fire Spacebar. - Weapons: forward bullets (velocity vector), 1s cooldown. - Health: 3 lives, shield regen, invincibility flash (1s post-hit). - Collision: with enemies/bullets loses 1 life. - UI: health bar top-left, score top-right. Integrate with game loop update/render. Balance: speed 200px/s, bullet speed 400px/s. Test controls and collisions.',
        'error_type': 'FeatureMissing'
    },
    {
        'source': 'shootymcshoot:missing_basic_enemies',
        'message': 'Missing basic enemy waves. Implement 2 types: 1. Scout: straight horizontal fly-in (right-to-left), 1HP, basic forward shots every 2s. 2. Weaver: sine-wave path (amplitude 50px, freq 0.02), 2HP, aimed player shots. Spawner: waves every 10s, increasing density. Enemy base class: position, velocity, hp, shoot(). Collision with player bullet destroys. Drop powerups optional. Enemy bullets: slow downward arc. Test wave progression, movement patterns, shooting accuracy. Ensure performance <16ms/frame.',
        'error_type': 'FeatureMissing'
    },
    {
        'source': 'shootymcshoot:missing_advanced_enemies',
        'message': 'Missing advanced enemies for difficulty ramp. 3 types: 1. Divebomber: straight dive toward player at y=300, 3HP, ramming attack. 2. Turret: stationary at random x, fires 3-way spread every 1.5s, 4HP. 3. Elite Fighter: erratic (random walk + player track), homing shots, 5HP. Integrate into spawner with % spawn rates increasing. Patterns: formations for turrets. Balance spawn after wave 3. Test AI behaviors, no overlaps, fair difficulty.',
        'error_type': 'FeatureMissing'
    },
    {
        'source': 'shootymcshoot:missing_boss',
        'message': 'Missing boss fight at level end (after 60s or 20 enemies). Boss: large entity center-screen, 1000HP bar top. Phases: 1. Slow left-right patrol, single shots. 2. (50%HP) Bullet hell spread + spawn scouts. 3. (25%HP) homing missiles + rapid fire. Defeat: victory screen. Behaviors: state machine, vulnerable core hitbox. Screen shake on hit. Test phases, balance ~2-3min fight. Victory transitions to menu/score.',
        'error_type': 'FeatureMissing'
    },
    {
        'source': 'shootymcshoot:missing_polish',
        'message': 'Missing polish/UI for production game. Add: - Score: enemy kills *100 + combos (x2 after 5s no death). - Particles: 20px explosion bursts (velocity scatter, fade). - Screens: Game Over (restart), Victory (stats, highscore localStorage). - SFX: Web Audio beeps/shoots (freq sweeps). - Parallax stars + nebula bg. - Screen shake, trail effects. - Pause overlay. Responsive canvas resize. Persist highscore. Test full flow.',
        'error_type': 'FeatureMissing'
    },
    {
        'source': 'shootymcshoot:missing_integration_docs',
        'message': 'Missing docs/arch updates post-implementation. Update: - docs/architecture/MAP.yaml modules.shootymcshoot summary to \\"R-Type style scrolling shooter\\". - DEPGRAPH.json edges if new deps. - docs/FRAMEWORK_OVERVIEW.md new section on ShootyMcShoot gameplay/features. - Test suite if applicable. Version bump pyproject.toml. Commit \\"feat(shootymcshoot): complete r-type game\\". Ensure health endpoint works, no regressions. Full e2e test via browser.',
        'error_type': 'FeatureMissing'
    }
]

for t in tickets_data:
    record_error(
        message=t['message'],
        source=t['source'],
        priority=TicketPriority.P2,
        error_type=t['error_type']
    )

print(f"Successfully raised 8 ShootyMcShoot game development tickets.")
