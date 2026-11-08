from swarm.concordia_lm import AdaptionLM


class _Mute:
    def complete(self, system, messages):
        return "I am thinking about it."  # never names an option


def test_choice_falls_back_uniformly_and_counts():
    lm = AdaptionLM.__new__(AdaptionLM)
    lm._b = _Mute()
    before = AdaptionLM.fallbacks
    picks = {lm.sample_choice("pick", ["a", "b", "c"], seed=s)[0] for s in range(30)}
    assert AdaptionLM.fallbacks - before == 30
    assert picks == {0, 1, 2}
