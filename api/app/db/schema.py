"""Database schema + migrations.

Port of server/src/db/schema.ts. The MIGRATIONS SQL is copied verbatim so the
Python backend operates on the exact same schema as the TypeScript backend.
"""
import sqlite3

from api.app.logger import info

MIGRATIONS: list[dict[str, str]] = [
    {
        "name": "001_initial_schema",
        "sql": """
      CREATE TABLE channels (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        subscriber_count INTEGER NOT NULL DEFAULT 0,
        thumbnail_url TEXT,
        fetched_at TEXT NOT NULL
      );

      CREATE TABLE videos (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        channel_id TEXT NOT NULL,
        channel_title TEXT NOT NULL,
        published_at TEXT NOT NULL,
        thumbnail_url TEXT NOT NULL,
        duration INTEGER NOT NULL,
        view_count INTEGER NOT NULL DEFAULT 0,
        like_count INTEGER NOT NULL DEFAULT 0,
        comment_count INTEGER NOT NULL DEFAULT 0,
        tags TEXT NOT NULL DEFAULT '[]',
        is_short INTEGER NOT NULL DEFAULT 1,
        fetched_at TEXT NOT NULL,
        FOREIGN KEY (channel_id) REFERENCES channels(id)
      );

      CREATE TABLE keyword_searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        time_range TEXT NOT NULL,
        language TEXT NOT NULL DEFAULT 'any',
        max_duration INTEGER NOT NULL DEFAULT 180,
        result_count INTEGER NOT NULL DEFAULT 0,
        searched_at TEXT NOT NULL
      );

      CREATE INDEX idx_keyword_searches_keyword ON keyword_searches(keyword, time_range);
      CREATE INDEX idx_keyword_searches_time ON keyword_searches(searched_at);

      CREATE TABLE keyword_search_results (
        search_id INTEGER NOT NULL,
        video_id TEXT NOT NULL,
        PRIMARY KEY (search_id, video_id),
        FOREIGN KEY (search_id) REFERENCES keyword_searches(id),
        FOREIGN KEY (video_id) REFERENCES videos(id)
      );

      CREATE TABLE keyword_suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        source TEXT NOT NULL,
        frequency INTEGER NOT NULL DEFAULT 1,
        parent_keyword TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
      );

      CREATE INDEX idx_keyword_suggestions_parent ON keyword_suggestions(parent_keyword);

      CREATE TABLE summaries (
        video_id TEXT NOT NULL,
        topic TEXT NOT NULL,
        hook_first_3_seconds TEXT NOT NULL,
        structure_hook TEXT NOT NULL,
        structure_body TEXT NOT NULL,
        structure_cta TEXT NOT NULL,
        style TEXT NOT NULL,
        key_moments TEXT NOT NULL DEFAULT '[]',
        confidence TEXT NOT NULL DEFAULT 'high',
        source_type TEXT NOT NULL DEFAULT 'transcript',
        prompt_version TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (video_id, prompt_version),
        FOREIGN KEY (video_id) REFERENCES videos(id)
      );

      CREATE TABLE collections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
      );

      CREATE TABLE collection_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        collection_id INTEGER NOT NULL,
        video_id TEXT NOT NULL,
        tags TEXT NOT NULL DEFAULT '[]',
        notes TEXT NOT NULL DEFAULT '',
        added_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
        FOREIGN KEY (video_id) REFERENCES videos(id),
        UNIQUE(collection_id, video_id)
      );
    """,
    },
    {
        "name": "002_campaigns_table",
        "sql": """
      CREATE TABLE IF NOT EXISTS campaigns (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        creator_or_brand TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'other',
        rate_per_k_views REAL NOT NULL,
        total_budget REAL NOT NULL,
        remaining_budget REAL NOT NULL,
        deadline TEXT,
        required_hashtags TEXT NOT NULL DEFAULT '[]',
        required_mentions TEXT NOT NULL DEFAULT '[]',
        allowed_platforms TEXT NOT NULL DEFAULT '["YouTube Shorts"]',
        target_keywords TEXT NOT NULL DEFAULT '[]',
        notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );

      CREATE INDEX IF NOT EXISTS idx_campaigns_category ON campaigns(category);

      -- Initial Seed Campaigns across popular Whop categories
      INSERT OR IGNORE INTO campaigns (
        id, name, creator_or_brand, category, rate_per_k_views, total_budget, remaining_budget,
        deadline, required_hashtags, required_mentions, allowed_platforms, target_keywords, notes, created_at, updated_at
      ) VALUES
      (
        'cmp_ai_saas',
        'AI Automation Studio Clip Rewards',
        'NextGen AI Lab',
        'ai_tech',
        4.50,
        5000.0,
        3850.0,
        date('now', '+20 days'),
        '["#aitools","#artificialintelligence","#techhacks"]',
        '["@NextGenAILab"]',
        '["YouTube Shorts","TikTok"]',
        '["ai tools","chatgpt","cara pakai ai","automation"]',
        'Klip demonstrasi software AI dan workflow otomatisasi.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_crypto_alpha',
        'BullRun Crypto Signals Campaign',
        'Alpha Trading Whop',
        'finance_crypto',
        6.00,
        8000.0,
        6400.0,
        date('now', '+25 days'),
        '["#cryptotrading","#bitcoin","#investasi"]',
        '["@AlphaWhop"]',
        '["YouTube Shorts"]',
        '["crypto trading","bitcoin","analisis crypto","cuan"]',
        'Gunakan rekaman cuplikan webinar & live trading resmi.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_dropship_hustle',
        'E-Com FastTrack Blueprint',
        'Hustle Mastery Academy',
        'business_sidehustle',
        3.50,
        3000.0,
        850.0,
        date('now', '+7 days'),
        '["#sidehustle","#bisnisonline","#dropshipping"]',
        '["@HustleAcademy"]',
        '["YouTube Shorts"]',
        '["side hustle","bisnis online","jualan online","modal kecil"]',
        'Budget mulai menipis, disarankan ambil aksi segera.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_gaming_stream',
        'Pro FPS Highlights Contest',
        'Apex Arena Club',
        'gaming',
        2.50,
        2500.0,
        1900.0,
        date('now', '+14 days'),
        '["#gamingmoments","#fpsgames","#streamerclips"]',
        '["@ApexArena"]',
        '["YouTube Shorts"]',
        '["gaming clips","gameplay lucu","clutch moment"]',
        'Klip momen seru dan funny moments dari gameplay streamer resmi.',
        datetime('now'),
        datetime('now')
      );
    """,
    },
    {
        "name": "003_add_campaign_url",
        "sql": """
      ALTER TABLE campaigns ADD COLUMN url TEXT NOT NULL DEFAULT '';

      UPDATE campaigns SET url = 'https://whop.com/discover/ai-automation-studio' WHERE id = 'cmp_ai_saas';
      UPDATE campaigns SET url = 'https://whop.com/discover/bullrun-crypto-alpha' WHERE id = 'cmp_crypto_alpha';
      UPDATE campaigns SET url = 'https://whop.com/discover/ecom-fasttrack' WHERE id = 'cmp_dropship_hustle';
      UPDATE campaigns SET url = 'https://whop.com/discover/apex-arena-fps' WHERE id = 'cmp_gaming_stream';
    """,
    },
    {
        "name": "004_populate_more_campaigns",
        "sql": """
      INSERT OR IGNORE INTO campaigns (
        id, name, creator_or_brand, category, url, rate_per_k_views, total_budget, remaining_budget,
        deadline, required_hashtags, required_mentions, allowed_platforms, target_keywords, notes, created_at, updated_at
      ) VALUES
      (
        'cmp_kling_ai',
        'Kling AI Video Generator Creator Bounty',
        'VisualAI Studio',
        'ai_tech',
        'https://whop.com/discover/kling-ai-creators',
        5.00,
        6000.0,
        5200.0,
        date('now', '+30 days'),
        '["#klingai","#aivideo","#generativeai"]',
        '["@VisualAIStudio"]',
        '["YouTube Shorts","TikTok"]',
        '["kling ai","ai video generator","tutorial ai video","text to video"]',
        'Demonstrasi hasil video AI realistis dan perbandingan prompt.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_code_assist',
        'CodeAssist Pro Developer Rewards',
        'DevStack Academy',
        'ai_tech',
        'https://whop.com/discover/codeassist-pro',
        4.20,
        4500.0,
        3700.0,
        date('now', '+21 days'),
        '["#codinghacks","#developerlife","#aitools"]',
        '["@DevStackAcademy"]',
        '["YouTube Shorts"]',
        '["coding ai","ai untuk programmer","belajar coding cepat","developer tools"]',
        'Klip tips coding cepat memakai coding assistant AI.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_forex_scalper',
        'Forex Scalper Elite Trading Hub',
        'FX Scalper Pro',
        'finance_crypto',
        'https://whop.com/discover/forex-scalper-elite',
        5.50,
        7500.0,
        6100.0,
        date('now', '+28 days'),
        '["#forextrading","#scalping","#daytrading"]',
        '["@FXScalperPro"]',
        '["YouTube Shorts"]',
        '["forex trading","strategi trading","scalping pemula","analisis forex"]',
        'Klip cuplikan live session profit trading & manajemen risiko.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_options_syndicate',
        'Options Trading Alpha Hub',
        'WallStreet Alpha Syndicate',
        'finance_crypto',
        'https://whop.com/discover/options-syndicate',
        6.20,
        5000.0,
        4250.0,
        date('now', '+18 days'),
        '["#optionstrading","#stocks","#investing"]',
        '["@AlphaSyndicate"]',
        '["YouTube Shorts"]',
        '["options trading","saham as","investasi saham pemula","cuan saham"]',
        'Edukasi ringkas breakdown pergerakan harga saham dan option calls.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_tiktok_affiliate',
        'TikTok Shop Affiliate Masterclass',
        'Commerce Mastery Network',
        'business_sidehustle',
        'https://whop.com/discover/tiktok-shop-accelerator',
        4.00,
        5500.0,
        4100.0,
        date('now', '+25 days'),
        '["#tiktokaffiliate","#bisnisdigital","#penghasilantambahan"]',
        '["@CommerceMastery"]',
        '["YouTube Shorts","TikTok"]',
        '["tiktok affiliate pemula","cara jualan tanpa stok","side hustle modal nol"]',
        'Klip studi kasus akun affiliate yang berhasil tembus omset dari nol.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_high_ticket_agency',
        'High-Ticket Remote Closing Club',
        'Apex Closer Guild',
        'business_sidehustle',
        'https://whop.com/discover/high-ticket-closing',
        3.80,
        4000.0,
        2900.0,
        date('now', '+15 days'),
        '["#remoteclosing","#freelance","#saleshacks"]',
        '["@ApexCloser"]',
        '["YouTube Shorts"]',
        '["remote closing","kerja remote dollar","freelance pemula","skill mahal"]',
        'Tips negosiasi dan percakapan sales closing dari rumah.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_roblox_creators',
        'Roblox Studio Creators Guild Contest',
        'BlockVerse Studios',
        'gaming',
        'https://whop.com/discover/roblox-creators-guild',
        2.80,
        3500.0,
        2600.0,
        date('now', '+20 days'),
        '["#robloxindonesia","#robloxdev","#robloxfunny"]',
        '["@BlockVerse"]',
        '["YouTube Shorts"]',
        '["roblox lucu","momen roblox","game roblox seru","roblox viral"]',
        'Klip lucu gameplay Roblox atau pamer karya game buatan sendiri di Roblox.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_minecraft_smp',
        'Minecraft SMP Lore & Clutches',
        'CraftMaster Realm',
        'gaming',
        'https://whop.com/discover/minecraft-smp-hub',
        2.60,
        3000.0,
        2400.0,
        date('now', '+22 days'),
        '["#minecraftclips","#minecraftbuilding","#smp"]',
        '["@CraftMaster"]',
        '["YouTube Shorts"]',
        '["minecraft lucu","trik minecraft","survival minecraft","momen clutch"]',
        'Klip momen seru, jebakan lucu, atau trik bangunan keren di Minecraft.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_calisthenics_iron',
        'IronForge Calisthenics & Gym Club',
        'IronForge Athletics',
        'fitness_lifestyle',
        'https://whop.com/discover/ironforge-calisthenics',
        3.50,
        4000.0,
        3100.0,
        date('now', '+25 days'),
        '["#calisthenics","#workoutpemula","#gymmotivation"]',
        '["@IronForgeAthletics"]',
        '["YouTube Shorts"]',
        '["workout di rumah","tips push up pemula","tips bentuk otot","kalistenik"]',
        'Klip koreksi form workout dan tips konsistensi latihan.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_glowup_habits',
        'Aesthetic Habits & Self-Improvement',
        'BetterYou Community',
        'fitness_lifestyle',
        'https://whop.com/discover/glowup-habits',
        3.00,
        3200.0,
        2650.0,
        date('now', '+30 days'),
        '["#selfimprovement","#glowup","#habits"]',
        '["@BetterYouWhop"]',
        '["YouTube Shorts"]',
        '["kebiasaan produktif","tips glow up pria","rutinitas pagi","self discipline"]',
        'Klip rutinitas harian aesthetic dan tips perbaikan diri praktis.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_keto_transformation',
        'Fasting & Biohacking Hub',
        'BioPeak Longevity',
        'fitness_lifestyle',
        'https://whop.com/discover/biohack-transformation',
        3.60,
        4200.0,
        3400.0,
        date('now', '+19 days'),
        '["#intermittentfasting","#biohacking","#polahidupsehat"]',
        '["@BioPeakWhop"]',
        '["YouTube Shorts"]',
        '["intermittent fasting pemula","turunkan berat badan","diet sehat","biohacking"]',
        'Klip penjelasan sains sederhana seputar puasa dan energi tubuh.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_cinema_breakdown',
        'CinemaReels Movie & Pop Culture Breakdown',
        'FilmTheory Vault',
        'entertainment',
        'https://whop.com/discover/cinemareels',
        3.20,
        4500.0,
        3600.0,
        date('now', '+28 days'),
        '["#filmtok","#moviereview","#popculture"]',
        '["@FilmTheoryVault"]',
        '["YouTube Shorts"]',
        '["bedah film","teori film bioskop","easter egg film","rekomendasi film"]',
        'Klip fakta tersembunyi dan bedah plot twist film populer.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_standup_viral',
        'Standup Comedy Highlights League',
        'LaughOutLoud Club',
        'entertainment',
        'https://whop.com/discover/standup-clips-whop',
        3.00,
        3800.0,
        2900.0,
        date('now', '+16 days'),
        '["#standupcomedy","#lucubanget","#punchline"]',
        '["@LOLComedyClub"]',
        '["YouTube Shorts"]',
        '["standup comedy lucu","roasting lucu","komedi indonesia","punchline pecah"]',
        'Klip punchline terlucu dari standup show resmi kreator.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_mystery_files',
        'True Crime & Dark Mystery Lore',
        'Chronicles of Mystery',
        'entertainment',
        'https://whop.com/discover/mystery-files-whop',
        3.40,
        5000.0,
        4300.0,
        date('now', '+24 days'),
        '["#truecrime","#misteridunia","#kisahnyata"]',
        '["@MysteryChronicles"]',
        '["YouTube Shorts"]',
        '["kasus misteri tak terpecahkan","kisah nyata merinding","fakta konspirasi"]',
        'Storytelling singkat kasus nyata dengan pacing cepat dan cliffhanger hook.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_notion_life_os',
        'Notion Life OS & Workspace Templates',
        'ZenProductivity Hub',
        'other',
        'https://whop.com/discover/notion-life-os',
        3.50,
        3000.0,
        2200.0,
        date('now', '+20 days'),
        '["#notiontemplate","#produktivitas","#lifeorganizer"]',
        '["@ZenProductivity"]',
        '["YouTube Shorts"]',
        '["template notion aesthetic","cara atur jadwal kuliah","produktivitas kerja"]',
        'Showcase screen record template Notion yang rapi dan fungsional.',
        datetime('now'),
        datetime('now')
      ),
      (
        'cmp_polyglot_fluency',
        'FluentFast Language Polyglot Club',
        'LingoHacks Global',
        'other',
        'https://whop.com/discover/fluentfast-languages',
        2.80,
        2500.0,
        1850.0,
        date('now', '+17 days'),
        '["#belajarbahasainggris","#polyglot","#bahasaasing"]',
        '["@LingoHacksGlobal"]',
        '["YouTube Shorts"]',
        '["tips lancar bahasa inggris","cara cepat hafal kosakata","belajar bahasa santai"]',
        'Tips trik belajar bahasa sehari-hari tanpa grammar rumit.',
        datetime('now'),
        datetime('now')
      );
    """,
    },
    {
        "name": "005_whop_sync_support",
        "sql": """
      ALTER TABLE campaigns ADD COLUMN spots_remaining INTEGER DEFAULT NULL;
      ALTER TABLE campaigns ADD COLUMN is_whop_live INTEGER NOT NULL DEFAULT 0;
      ALTER TABLE campaigns ADD COLUMN whop_goal_type TEXT DEFAULT NULL;

      CREATE TABLE IF NOT EXISTS whop_sync_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        synced_at TEXT NOT NULL,
        campaigns_count INTEGER NOT NULL,
        status TEXT NOT NULL,
        error_message TEXT
      );

      CREATE INDEX IF NOT EXISTS idx_whop_sync_logs_synced_at ON whop_sync_logs(synced_at DESC);
    """,
    },
    {
        "name": "006_clips",
        "sql": """
      CREATE TABLE IF NOT EXISTS clip_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_type TEXT NOT NULL,
        source_ref TEXT NOT NULL,
        title TEXT,
        duration_seconds REAL,
        local_path TEXT,
        transcript_path TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        error_message TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS clips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        reason TEXT,
        start_seconds REAL NOT NULL,
        end_seconds REAL NOT NULL,
        mode TEXT NOT NULL DEFAULT 'crop',
        subtitles INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'pending',
        output_path TEXT,
        error_message TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (source_id) REFERENCES clip_sources(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_clips_source_id ON clips(source_id);
      CREATE INDEX IF NOT EXISTS idx_clip_sources_created_at ON clip_sources(created_at DESC);
    """,
    },
]


def _split_statements(sql: str) -> list[str]:
    """Split a SQL script on semicolons while respecting string literals and
    `--` line comments.

    sqlite3's executescript() issues an implicit COMMIT before running, which
    would break our explicit migration transaction, so we split and execute
    each statement individually instead.
    """
    statements: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(sql)
    while i < n:
        ch = sql[i]
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            i += 1
            while i < n:
                buf.append(sql[i])
                if sql[i] == quote:
                    # Handle escaped quote by doubling (e.g. '').
                    if quote == "'" and i + 1 < n and sql[i + 1] == "'":
                        buf.append(sql[i + 1])
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            continue
        if ch == "-" and i + 1 < n and sql[i + 1] == "-":
            while i < n and sql[i] != "\n":
                i += 1
            continue
        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def run_migrations(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS _migrations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE,
          applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    applied = {row["name"] for row in conn.execute("SELECT name FROM _migrations").fetchall()}

    for migration in MIGRATIONS:
        if migration["name"] not in applied:
            info("Running migration", {"name": migration["name"]})
            statements = _split_statements(migration["sql"])
            conn.execute("BEGIN")
            try:
                for statement in statements:
                    conn.execute(statement)
                conn.execute("INSERT INTO _migrations (name) VALUES (?)", (migration["name"],))
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise

    info("All migrations applied")