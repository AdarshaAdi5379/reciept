"""
Number to Words Conversion Utility.
Converts numeric values to Indian English words.
"""
from typing import Union


class NumberToWords:
    """Convert numbers to words in Indian English format."""
    
    ONES = [
        '', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
        'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
        'Seventeen', 'Eighteen', 'Nineteen'
    ]
    
    TENS = [
        '', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'
    ]
    
    SCALE = [
        '', 'Thousand', 'Lakh', 'Crore'
    ]
    
    @staticmethod
    def convert_hundreds(num: int) -> str:
        """Convert numbers 0-999 to words."""
        if num == 0:
            return ''
        elif num < 20:
            return NumberToWords.ONES[num]
        elif num < 100:
            tens_digit = num // 10
            ones_digit = num % 10
            if ones_digit == 0:
                return NumberToWords.TENS[tens_digit]
            else:
                return NumberToWords.TENS[tens_digit] + ' ' + NumberToWords.ONES[ones_digit]
        else:
            hundreds_digit = num // 100
            remainder = num % 100
            result = NumberToWords.ONES[hundreds_digit] + ' Hundred'
            if remainder > 0:
                result += ' ' + NumberToWords.convert_hundreds(remainder)
            return result
    
    @staticmethod
    def to_words(amount: Union[int, float]) -> str:
        """
        Convert amount to words in Indian format.
        
        Examples:
            20000 -> "Twenty Thousand"
            123456 -> "One Lakh Twenty Three Thousand Four Hundred Fifty Six"
            1000000 -> "Ten Lakh"
            10000000 -> "One Crore"
        """
        # Handle decimal amounts
        if isinstance(amount, float):
            whole = int(amount)
            paise = round((amount - whole) * 100)
        else:
            whole = int(amount)
            paise = 0
        
        if whole == 0:
            words = 'Zero'
        elif whole < 100:
            words = NumberToWords.convert_hundreds(whole)
        else:
            parts = []
            scale_index = 0
            
            # Process in groups of 2 digits (for Indian numbering)
            while whole > 0:
                if scale_index == 0:
                    # Last 3 digits (ones, tens, hundreds)
                    group = whole % 1000
                    whole //= 1000
                else:
                    # Next 2 digits
                    group = whole % 100
                    whole //= 100
                
                if group > 0:
                    group_words = NumberToWords.convert_hundreds(group)
                    if scale_index < len(NumberToWords.SCALE):
                        scale = NumberToWords.SCALE[scale_index]
                        if scale:
                            group_words += ' ' + scale
                    parts.append(group_words)
                
                scale_index += 1
            
            words = ' '.join(reversed(parts))
        
        # Add "Only" at the end as per Indian conventions
        return words + ' Only'
    
    @staticmethod
    def rupees_and_paise(amount: Union[int, float]) -> dict:
        """
        Split amount into rupees and paise.
        
        Returns:
            Dictionary with 'rupees', 'paise', 'words', 'formatted'
        """
        if isinstance(amount, float):
            whole = int(amount)
            paise = round((amount - whole) * 100)
        else:
            whole = int(amount)
            paise = 0
        
        return {
            'rupees': whole,
            'paise': paise,
            'words': NumberToWords.to_words(amount),
            'formatted': f'₹ {whole}.{paise:02d}',
        }


def amount_in_words(amount: Union[int, float]) -> str:
    """
    Convenience function to convert amount to words.
    
    Args:
        amount: Numeric amount
        
    Returns:
        Amount in words with "Only" suffix
    """
    return NumberToWords.to_words(amount)


def rupees_and_paise(amount: Union[int, float]) -> dict:
    """
    Convenience function to split amount.
    
    Args:
        amount: Numeric amount
        
    Returns:
        Dictionary with rupees, paise, and words
    """
    return NumberToWords.rupees_and_paise(amount)
