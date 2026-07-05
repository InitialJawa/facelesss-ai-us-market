import asyncio
from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from datetime import datetime

from pipeline.orchestrator import PipelineOrchestrator
from pipeline.queue import PipelineQueue
from brain.manager import Brain
from app.config import settings

console = Console()

TITLE = """
╔══════════════════════════════════════════╗
║           FACELess AI                    ║
║         Media Factory v0.1               ║
╚══════════════════════════════════════════╝
"""

MENU_ITEMS = [
    ("1", "Generate 1 Video", "Buat satu video dari topik baru"),
    ("2", "Generate 10 Videos", "Buat 10 video sekaligus"),
    ("3", "Generate Today Schedule", "Generate sesuai jadwal hari ini"),
    ("4", "Upload Pending", "Upload video yang siap tapi belum di-upload"),
    ("5", "Analyze Channel", "Analisis performa channel & update Brain"),
    ("6", "Resume Failed Jobs", "Lanjutkan job yang gagal"),
    ("7", "View Queue Status", "Lihat status antrian"),
    ("8", "Brain Insights", "Lihat apa yang sudah dipelajari Brain"),
    ("9", "Run Continuous", "Jalankan pipeline otomatis"),
    ("0", "Exit", "Keluar"),
]


class MediaFactoryCLI:
    def __init__(self):
        self.brain = Brain(settings.brain_dir)
        self.brain.load()
        self.queue = PipelineQueue(settings.queue_db_path)
        self.orchestrator = PipelineOrchestrator(self.brain, self.queue)
        self._continuous_task = None

    def show_header(self):
        console.clear()
        console.print(TITLE, style="bold cyan")
        console.print(
            Panel.fit(
                f"[dim]Brain:[/dim] {len(self.brain.memory)} modules loaded\n"
                f"[dim]Queue:[/dim] {self.queue.get_status()['total']} jobs\n"
                f"[dim]Mode:[/dim] CLI Interactive\n"
                f"[dim]Time:[/dim] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                title="[bold green]Status[/bold green]",
                border_style="green",
            )
        )
        console.print()

    def show_menu(self):
        table = Table(show_header=False, border_style="blue", box=None)
        table.add_column("Key", style="bold yellow", width=6)
        table.add_column("Action", style="bold white", width=30)
        table.add_column("Description", style="dim", width=40)

        for key, action, desc in MENU_ITEMS:
            table.add_row(key, action, desc)

        console.print(table)
        console.print()

    def run(self):
        while True:
            self.show_header()
            self.show_menu()
            choice = Prompt.ask(
                "[bold cyan]Pilih menu[/bold cyan]",
                choices=[str(i) for i in range(10)],
                default="0",
            )

            if choice == "0":
                console.print("[bold red]Keluar...[/bold red]")
                break
            elif choice == "1":
                self._generate_single()
            elif choice == "2":
                self._generate_batch(10)
            elif choice == "3":
                self._generate_schedule()
            elif choice == "4":
                asyncio.run(self._upload_pending())
            elif choice == "5":
                asyncio.run(self._analyze_channel())
            elif choice == "6":
                asyncio.run(self._resume_failed())
            elif choice == "7":
                self._show_queue()
            elif choice == "8":
                self._show_brain()
            elif choice == "9":
                asyncio.run(self._run_continuous())

    def _generate_single(self):
        topic = Prompt.ask("[bold yellow]Topik video[/bold yellow]")
        if not topic:
            return
        job_id = self.orchestrator.create_job(topic)
        console.print(f"[green]✓[/green] Job dibuat: [bold]{job_id[:8]}...[/bold]")
        run_now = Prompt.ask(
            "[bold]Proses sekarang?[/bold]", choices=["y", "n"], default="y"
        )
        if run_now == "y":
            success = asyncio.run(self.orchestrator.process_job(job_id))
            if success:
                console.print("[green]✓ Video selesai diproses![/green]")
            else:
                console.print("[red]✗ Gagal memproses video[/red]")
        Prompt.ask("[dim]Tekan Enter untuk lanjut[/dim]")

    def _generate_batch(self, count: int):
        console.print(f"[bold]Generate {count} video[/bold]")
        niche = Prompt.ask("[bold yellow]Niche[/bold yellow]", default="general")
        for i in range(count):
            topic = Prompt.ask(
                f"[bold]Topik video ke-{i+1}[/bold]", default=f"{niche} topic {i+1}"
            )
            if topic:
                self.orchestrator.create_job(topic, niche=niche)
        console.print(f"[green]✓ {count} job ditambahkan ke queue[/green]")
        run_now = Prompt.ask(
            "[bold]Proses semua sekarang?[/bold]", choices=["y", "n"], default="y"
        )
        if run_now == "y":
            asyncio.run(self.orchestrator.process_pending(count))
            console.print("[green]✓ Batch processing selesai[/green]")
        Prompt.ask("[dim]Tekan Enter untuk lanjut[/dim]")

    def _generate_schedule(self):
        console.print("[bold]Generate Today Schedule[/bold]")
        count = IntPrompt.ask(
            "Jumlah video hari ini", default=settings.uploads_per_day
        )
        niche = Prompt.ask("Niche", default="general")
        for i in range(count):
            self.orchestrator.create_job(
                f"{niche} scheduled #{i+1}", niche=niche
            )
        console.print(f"[green]✓ {count} job untuk jadwal hari ini dibuat[/green]")
        Prompt.ask("[dim]Tekan Enter untuk lanjut[/dim]")

    async def _upload_pending(self):
        console.print("[bold]Upload Pending[/bold]")
        console.print("[yellow]Belum terimplementasi (butuh YouTube API)[/yellow]")
        Prompt.ask("[dim]Tekan Enter untuk lanjut[/dim]")

    async def _analyze_channel(self):
        console.print("[bold]Analyze Channel[/bold]")
        console.print("[yellow]Belum terimplementasi (butuh YouTube API)[/yellow]")
        Prompt.ask("[dim]Tekan Enter untuk lanjut[/dim]")

    async def _resume_failed(self):
        console.print("[bold]Resume Failed Jobs[/bold]")
        jobs = self.queue.resume_all()
        if jobs:
            console.print(f"[green]✓ {len(jobs)} job siap diproses ulang[/green]")
            process = Prompt.ask(
                "Proses sekarang?", choices=["y", "n"], default="y"
            )
            if process == "y":
                await self.orchestrator.process_pending(len(jobs))
                console.print("[green]✓ Selesai[/green]")
        else:
            console.print("[yellow]Tidak ada job yang perlu di-resume[/yellow]")
        Prompt.ask("[dim]Tekan Enter untuk lanjut[/dim]")

    def _show_queue(self):
        status = self.queue.get_status()
        table = Table(title="Queue Status", border_style="blue")
        table.add_column("Status", style="bold")
        table.add_column("Count", style="numeric")
        for k, v in status.items():
            if k != "total":
                table.add_row(k.capitalize(), str(v))
        table.add_row("[bold]Total[/bold]", str(status["total"]))
        console.print(table)
        Prompt.ask("[dim]Tekan Enter untuk lanjut[/dim]")

    def _show_brain(self):
        brain_data = self.brain.to_dict()
        table = Table(title="🧠 Brain Insights", border_style="green")
        table.add_column("Module", style="bold cyan")
        table.add_column("Key Insights", style="white")

        for module, data in brain_data.items():
            insights = []
            if isinstance(data, dict):
                for k, v in list(data.items())[:3]:
                    if isinstance(v, list) and v:
                        insights.append(f"[dim]{k}:[/dim] {v[:3]}")
                    elif isinstance(v, (int, float)) and v:
                        insights.append(f"[dim]{k}:[/dim] {v}")
                    elif isinstance(v, str) and v:
                        insights.append(f"[dim]{k}:[/dim] {v[:50]}")
            table.add_row(
                f"[bold]{module}[/bold]",
                "\n".join(insights) if insights else "[dim]empty[/dim]",
            )
        console.print(table)
        Prompt.ask("[dim]Tekan Enter untuk lanjut[/dim]")

    async def _run_continuous(self):
        console.print("[bold green]Running continuous pipeline...[/bold green]")
        console.print("[dim]Tekan Ctrl+C untuk berhenti[/dim]")
        try:
            await self.orchestrator.run_continuous(interval=30)
        except KeyboardInterrupt:
            self.orchestrator.stop()
            console.print("\n[bold yellow]Pipeline dihentikan[/bold yellow]")
        Prompt.ask("[dim]Tekan Enter untuk lanjut[/dim]")
