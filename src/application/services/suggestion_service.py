from fastapi import Depends

from src.application.services.llm_service import LLMService
from src.infrastructure.models.virtual_machine import VirtualMachine
from src.infrastructure.models.vm_suggestion import SuggestionStatus, VmSuggestion
from src.infrastructure.repositories.vm_metrics import VmMetricsRepository
from src.infrastructure.repositories.vm_suggestion import VmSuggestionRepository


class SuggestionService:
    def __init__(
        self,
        suggestion_repo: VmSuggestionRepository = Depends(),
        metrics_repo: VmMetricsRepository = Depends(),
        llm: LLMService = Depends(),
    ) -> None:
        self._suggestions = suggestion_repo
        self._metrics = metrics_repo
        self._llm = llm

    async def analyze_and_suggest(self, vm: VirtualMachine) -> VmSuggestion | None:
        """
        Fetch last 7 days of metrics, ask LLM for an optimization suggestion.
        Skips if fewer than 5 data points or confidence < 0.7.
        """
        metrics = await self._metrics.get_recent(vm.id, hours=168)
        if len(metrics) < 5:
            return None

        avg_cpu = sum(m.cpu_pct for m in metrics) / len(metrics)
        avg_ram = sum(m.ram_pct for m in metrics) / len(metrics)
        max_disk = max(m.disk_pct for m in metrics)

        prompt = (
            f"VM: {vm.vcpu} vCPU / {vm.ram_mb} MB RAM / {vm.disk_gb} GB disk\n"
            f"7-day averages: CPU={avg_cpu:.1f}% RAM={avg_ram:.1f}% Disk max={max_disk:.1f}%\n"
            "Suggest an optimization if there is a clear opportunity."
        )

        result = await self._llm.suggest_optimization(prompt)
        if result.get("confidence", 0) < 0.7:
            return None

        return await self._suggestions.create(
            vm_id=vm.id,
            tenant_id=vm.tenant_id,
            suggestion_text=result["text"],
            suggested_config=result.get("config"),
            confidence=result["confidence"],
        )

    async def get_pending(self, vm_id) -> list[VmSuggestion]:
        return await self._suggestions.get_pending(vm_id=vm_id)

    async def accept(self, suggestion_id, vm_id) -> VmSuggestion | None:
        return await self._suggestions.set_status(suggestion_id, SuggestionStatus.ACCEPTED)

    async def dismiss(self, suggestion_id, vm_id) -> VmSuggestion | None:
        return await self._suggestions.set_status(suggestion_id, SuggestionStatus.DISMISSED)
