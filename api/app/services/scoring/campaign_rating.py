"""Campaign opportunity & target-feasibility rating.

Port of server/src/services/scoring/campaign-rating.ts.
"""
import math

from api.app.lib.format import js_number_to_string, js_round, to_id_string

NICHE_BENCHMARKS: dict[str, dict] = {
    "ai_tech": {
        "demandScore": 88,
        "viralityScore": 92,
        "label": "Viralitas Sangat Tinggi",
        "audienceSize": "Mass Appeal (Semua Kalangan)",
        "tips": [
            "Gunakan format demonstrasi Before vs After dalam 2 detik pertama.",
            "Sebutkan nama tool AI gratis atau fitur unik yang memicu rasa penasaran.",
            "Tampilkan teks call-to-action link di bio/caption.",
        ],
    },
    "gaming": {
        "demandScore": 85,
        "viralityScore": 95,
        "label": "Sangat Mudah FYP",
        "audienceSize": "Masif & Cepat Viral",
        "tips": [
            "Pilih momen paling heboh (clutch, fail, funny moment) langsung di detik 0.",
            "Tambahkan sound effect atau zoom-in ekspresi streamer.",
            "Targetkan views cepat di 3 jam pertama setelah upload.",
        ],
    },
    "entertainment": {
        "demandScore": 85,
        "viralityScore": 90,
        "label": "Viralitas Tinggi",
        "audienceSize": "Sangat Luas",
        "tips": [
            "Buka dengan pertanyaan kontroversial atau hook emosional.",
            "Jaga ritme edit cepat dengan potongan setiap 1-2 detik.",
        ],
    },
    "business_sidehustle": {
        "demandScore": 84,
        "viralityScore": 82,
        "label": "Tinggi untuk Pencari Cuan",
        "audienceSize": "Pencari Passive Income",
        "tips": [
            'Tampilkan angka/hasil konkret di detik awal (misal: "Hasilkan $50/hari dari rumah").',
            "Hindari penjelasan berbelit; langsung ke tutorial langkah 1.",
        ],
    },
    "finance_crypto": {
        "demandScore": 90,
        "viralityScore": 72,
        "label": "Rate Tinggi, Niche Tertarget",
        "audienceSize": "Niche Spesifik",
        "tips": [
            "Gunakan istilah sederhana yang dipahami pemula (hindari jargon berat).",
            "Sorot momentum market atau berita trending crypto terbaru.",
            "Rate per views sangat besar, jadi tidak butuh jutaan views untuk hasil besar.",
        ],
    },
    "fitness_lifestyle": {
        "demandScore": 78,
        "viralityScore": 80,
        "label": "Menengah ke Tinggi",
        "audienceSize": "Gaya Hidup & Kesehatan",
        "tips": [
            "Fokus pada tips cepat (misal: kesalahan umum saat workout).",
            "Visual sebelum & sesudah sangat efektif menarik retensi.",
        ],
    },
    "other": {
        "demandScore": 70,
        "viralityScore": 70,
        "label": "Standar",
        "audienceSize": "Bervariasi",
        "tips": [
            "Uji coba beberapa variasi hook di 3 detik pertama.",
            "Pastikan caption dan hashtag sesuai ketentuan campaign.",
        ],
    },
}


def calculate_campaign_rating(campaign: dict) -> dict:
    rate = max(0.1, campaign["ratePerKViews"])
    niche = NICHE_BENCHMARKS.get(campaign.get("category")) or NICHE_BENCHMARKS["other"]

    # 1. Earning score (0-100) based on rate per 1K views (RPM)
    earning_score = min(100, js_round((rate / 5.5) * 100))

    # 2. Budget health score & safety
    remaining = campaign["remainingBudget"]
    budget_score = 50
    budget_health = "moderate"
    budget_runway_score = 60
    if remaining >= 2500:
        budget_score, budget_health, budget_runway_score = 100, "safe", 100
    elif remaining >= 1200:
        budget_score, budget_health, budget_runway_score = 80, "safe", 85
    elif remaining >= 500:
        budget_score, budget_health, budget_runway_score = 60, "moderate", 60
    else:
        budget_score, budget_health, budget_runway_score = 30, "low", 25

    # 3. Demand score
    demand_score = niche["demandScore"]

    # 4. Views needed for target earnings
    views_for_25 = math.ceil((25 / rate) * 1000)
    views_for_50 = math.ceil((50 / rate) * 1000)
    views_for_100 = math.ceil((100 / rate) * 1000)

    # 5. Target feasibility / ease score
    if views_for_50 <= 10000:
        views_burden_score = 100
    elif views_for_50 <= 15000:
        views_burden_score = 85
    elif views_for_50 <= 25000:
        views_burden_score = 70
    elif views_for_50 <= 40000:
        views_burden_score = 50
    else:
        views_burden_score = 25

    raw_ease_score = (
        views_burden_score * 0.40 + niche["viralityScore"] * 0.35 + budget_runway_score * 0.25
    )
    target_ease_score = min(100, max(0, js_round(raw_ease_score)))

    if target_ease_score >= 80:
        target_ease_level = "very_easy"
    elif target_ease_score >= 65:
        target_ease_level = "easy"
    elif target_ease_score >= 50:
        target_ease_level = "moderate"
    else:
        target_ease_level = "hard"

    budget_safety_pockets = max(0, math.floor(remaining / 50))

    remaining_str = js_number_to_string(remaining)
    if target_ease_level == "very_easy":
        ease_explanation = (
            f"\U0001f3af Sangat Mudah: Cukup butuh {to_id_string(views_for_50)} views untuk target "
            f"$50 di niche {niche['label']} dengan sisa budget sangat aman "
            f"({budget_safety_pockets} slot payout tersisa)."
        )
    elif target_ease_level == "easy":
        ease_explanation = (
            f"\U0001f680 Mudah Dicapai: Butuh {to_id_string(views_for_50)} views untuk $50. "
            f"Niche {campaign['category']} memiliki audience luas dan budget masih mencukupi."
        )
    elif target_ease_level == "moderate":
        ease_explanation = (
            f"\u2696\ufe0f Sedang: Membutuhkan {to_id_string(views_for_50)} views. Perlu hook kuat "
            f"di 3 detik pertama agar klip menembus algoritma."
        )
    else:
        ease_explanation = (
            f"\u26a0\ufe0f Butuh Effort Ekstra: Memerlukan {to_id_string(views_for_50)} views atau "
            f"sisa budget menipis (${remaining_str}), berisiko kehabisan budget sebelum target tercapai."
        )

    # 6. Weighted total opportunity score
    raw_score = (
        earning_score * 0.25
        + budget_score * 0.20
        + demand_score * 0.20
        + target_ease_score * 0.35
    )
    opportunity_score = js_round(raw_score)

    # 7. Tier
    if opportunity_score >= 80:
        tier = "S"
        verdict = "\U0001f525 Rekomendasi Utama: Sangat mudah tembus target dan potensi pendapatan tinggi!"
    elif opportunity_score >= 65:
        tier = "A"
        verdict = "\U0001f680 Sangat Potensial: Peluang target tercapai tinggi dengan estimasi payout menguntungkan."
    elif opportunity_score >= 50:
        tier = "B"
        verdict = "\u2696\ufe0f Potensi Menengah: Target bisa dicapai dengan optimasi hook klip yang menarik."
    else:
        tier = "C"
        verdict = "\u26a0\ufe0f Kurang Direkomendasikan: Target lebih sulit dicapai atau sisa budget menipis."

    # 8. Projected earnings simulation
    projected_earnings = {
        "views10k": js_round(10 * rate),
        "views50k": js_round(50 * rate),
        "views100k": js_round(100 * rate),
        "views500k": js_round(500 * rate),
    }

    return {
        "campaignId": campaign["id"],
        "tier": tier,
        "opportunityScore": opportunity_score,
        "earningScore": earning_score,
        "demandScore": demand_score,
        "budgetScore": budget_score,
        "projectedEarnings": projected_earnings,
        "budgetHealth": budget_health,
        "verdict": verdict,
        "targetEaseLevel": target_ease_level,
        "targetEaseScore": target_ease_score,
        "viewsNeededForTarget": {
            "for25USD": views_for_25,
            "for50USD": views_for_50,
            "for100USD": views_for_100,
        },
        "nicheVirality": {
            "score": niche["viralityScore"],
            "label": niche["label"],
            "audienceSize": niche["audienceSize"],
        },
        "budgetSafetyPockets": budget_safety_pockets,
        "easeExplanation": ease_explanation,
        "strategyTips": niche["tips"],
    }