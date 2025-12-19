import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Import your model and utility functions
from .models import Wallet
from .utils import (
    generate_bsc_wallet,
    send_bnb_safe,
    send_bep20_token_safe,
    EXAMPLE_TOKEN_ADDRESS
)


# --- WEB PAGES ---

def index(request):
    """Main dashboard page."""
    # We pass all saved wallets to the template so you can see them in a list
    saved_wallets = Wallet.objects.all().order_by('-id')
    return render(request, 'bscapp/index.html', {
        'example_token_address': EXAMPLE_TOKEN_ADDRESS,
        'saved_wallets': saved_wallets
    })


def diagnostic_view(request):
    """Simple check to see if the server is running."""
    return HttpResponse("<h1>Diagnostic Page</h1><p>The BSC Wallet Manager is online.</p>")


# --- API ENDPOINTS ---

@csrf_exempt
def api_generate_wallet(request):
    """
    Generates a wallet, saves ALL data to SQLite, and returns JSON.
    Matches the generate_bsc_wallet() return structure.
    """
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

    try:
        # 1. Generate the wallet data using utils
        data = generate_bsc_wallet()

        # 2. SAVE to the SQLite database using the Wallet model
        # Make sure your models.py has these exact fields!
        Wallet.objects.create(
            mnemonic=data["mnemonic"],
            private_key=data["private_key"],
            public_key=data["public_key"],
            address=data["bsc_testnet_address"],
            derivation_path=data["derivation_path"]
        )

        # 3. Return the data to your UI
        return JsonResponse({"status": "success", "data": data})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def api_send_bnb(request):
    """Handles native tBNB transfers."""
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)
    try:
        body = json.loads(request.body)
        result = send_bnb_safe(
            body.get('private_key'),
            body.get('recipient_address'),
            body.get('amount')
        )
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@csrf_exempt
def api_send_token(request):
    """Handles BEP-20 token transfers."""
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)
    try:
        body = json.loads(request.body)
        result = send_bep20_token_safe(
            body.get('private_key'),
            body.get('token_address'),
            body.get('receiver_address'),
            body.get('amount')
        )
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)