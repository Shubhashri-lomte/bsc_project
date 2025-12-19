import pytest
from unittest.mock import patch, MagicMock
from bscapp.utils import *

# --- Mock Data ---
FAKE_PVT_KEY = "0x45cd12c3f8e5f67a83d6a9e8c76b5d4e3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d"
FAKE_RECEIVER = "0x0000000000000000000000000000000000000000"


class TestWalletValidation:

    @patch('bscapp.utils.w3.eth.get_balance')
    def test_insufficient_balance_under_1_bnb(self, mock_balance):
        """Test that validation fails if balance is 0.5 BNB"""
        # Set mock balance to 0.5 BNB in Wei
        mock_balance.return_value = w3.to_wei(0.5, 'ether')

        result = send_bnb_safe(FAKE_PVT_KEY, FAKE_RECEIVER, 0.1)

        assert result['status'] == 'error'
        assert "Minimum 1 BNB required" in result['message']

    @patch('bscapp.utils.w3.eth.get_balance')
    def test_zero_balance_failure(self, mock_balance):
        """Test that validation fails if balance is 0"""
        mock_balance.return_value = 0

        result = send_bnb_safe(FAKE_PVT_KEY, FAKE_RECEIVER, 0.1)

        assert result['status'] == 'error'
        assert "Minimum 1 BNB required" in result['message']

    @patch('bscapp.utils.w3.eth.get_balance')
    @patch('bscapp.utils.w3.eth.get_transaction_count')
    @patch('bscapp.utils.w3.eth.account.sign_transaction')
    @patch('bscapp.utils.w3.eth.send_raw_transaction')
    @patch('bscapp.utils.w3.eth.wait_for_transaction_receipt')
    def test_successful_validation_over_1_bnb(self, mock_wait, mock_send, mock_sign, mock_nonce, mock_balance):
        """Test that validation passes if balance is 1.5 BNB"""
        # 1. Setup Mocks
        mock_balance.return_value = w3.to_wei(1.5, 'ether')
        mock_nonce.return_value = 0
        mock_sign.return_value.raw_transaction = b'fake_signed_tx'
        mock_send.return_value = MagicMock(hex=lambda: "0xhash")

        # 2. Execute
        result = send_bnb_safe(FAKE_PVT_KEY, FAKE_RECEIVER, 0.1)

        # 3. Assertions
        assert result['status'] == 'success'
        assert "tx_hash" in result
