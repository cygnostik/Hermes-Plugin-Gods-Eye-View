"""GEV onboarding CLI. Registration performs no I/O or installation."""


def _setup_cli(parser):
    commands = parser.add_subparsers(dest="gev_command", required=True)
    configure = commands.add_parser("configure", help="Use an existing official GEV checkout and Node runtime")
    configure.add_argument("--root", required=True, help="Existing official bilawalsidhu/gods-eye-view checkout")
    configure.add_argument("--node", required=True, help="Path to the Node executable (node.exe on Windows)")
    configure.add_argument("--npm-cli", help="Path to npm-cli.js; otherwise derived from the Node installation")
    configure.add_argument("--port", type=int, default=4173)


def _handle_cli(args):
    import importlib.util
    import json
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("gev_cli_settings", Path(__file__).with_name("settings.py"))
    settings = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settings)
    try:
        result = settings.configure(args.root, args.node, args.npm_cli, args.port)
    except (ValueError, OSError) as exc:
        print(f"GEV configuration failed: {exc}")
        raise SystemExit(1) from None
    print(json.dumps(result, indent=2))
    return 0


def register(ctx) -> None:
    ctx.register_cli_command(
        name="gev", help="Configure God's Eye View for this Hermes profile",
        setup_fn=_setup_cli, handler_fn=_handle_cli,
        description="Connect an existing official GEV checkout; never downloads or installs software.",
    )
