from apps.activities.models import Tag


class LocalTagProvider:
    def suggest(self, activity):
        tags = list(Tag.objects.filter(is_active=True).order_by("sort_order", "id")[:3])
        return [{"tag": tag, "confidence": 0.5, "reason": "本地规则候选"} for tag in tags]


def run_ai_tagging(review, provider=None, force_failure=False):
    if force_failure:
        raise RuntimeError("本地 AI provider 执行失败")
    provider = provider or LocalTagProvider()
    return provider.suggest(review.activity)
