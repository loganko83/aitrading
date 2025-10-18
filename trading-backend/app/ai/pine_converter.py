"""
Pine Script to Python Converter

AI-powered converter that transforms TradingView Pine Script indicators
into Python pandas/numpy code compatible with our backtesting system.
"""

import re
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConversionResult:
    """Result of Pine Script conversion"""
    success: bool
    python_code: str
    function_name: str
    description: str
    parameters: Dict[str, any]
    error_message: Optional[str] = None
    warnings: list = None


class PineScriptConverter:
    """
    Converts Pine Script indicators to Python code

    Uses GPT-4 for intelligent code transformation with validation.
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize converter

        Args:
            openai_api_key: OpenAI API key (defaults to env variable)
        """
        self.api_key = openai_api_key
        self.warnings = []

    async def convert_to_python(
        self,
        pine_script: str,
        indicator_name: Optional[str] = None
    ) -> ConversionResult:
        """
        Convert Pine Script to Python pandas/numpy code

        Args:
            pine_script: Pine Script source code
            indicator_name: Optional custom name for the indicator

        Returns:
            ConversionResult with Python code and metadata
        """
        try:
            # Step 1: Analyze Pine Script
            analysis = self._analyze_pine_script(pine_script)

            # Step 2: Extract metadata
            metadata = self._extract_metadata(pine_script)

            # Step 3: Generate Python code using AI
            python_code = await self._generate_python_code(
                pine_script=pine_script,
                analysis=analysis,
                metadata=metadata,
                custom_name=indicator_name
            )

            # Step 4: Validate generated code
            validation = self._validate_python_code(python_code)

            if not validation['valid']:
                return ConversionResult(
                    success=False,
                    python_code="",
                    function_name="",
                    description="",
                    parameters={},
                    error_message=validation['error'],
                    warnings=self.warnings
                )

            # Step 5: Extract function details
            func_name = self._extract_function_name(python_code)
            params = self._extract_parameters(python_code)

            return ConversionResult(
                success=True,
                python_code=python_code,
                function_name=func_name,
                description=metadata.get('description', 'Converted from Pine Script'),
                parameters=params,
                warnings=self.warnings
            )

        except Exception as e:
            logger.error(f"Conversion error: {str(e)}", exc_info=True)
            return ConversionResult(
                success=False,
                python_code="",
                function_name="",
                description="",
                parameters={},
                error_message=f"Conversion failed: {str(e)}",
                warnings=self.warnings
            )

    def _analyze_pine_script(self, code: str) -> Dict:
        """Analyze Pine Script code structure"""
        analysis = {
            'has_study': 'study(' in code or 'indicator(' in code,
            'has_strategy': 'strategy(' in code,
            'has_plot': 'plot(' in code or 'plotshape(' in code,
            'has_alertcondition': 'alertcondition(' in code,
            'uses_security': 'security(' in code,
            'version': self._detect_version(code),
            'inputs': self._find_inputs(code),
            'calculations': self._find_calculations(code)
        }

        return analysis

    def _detect_version(self, code: str) -> int:
        """Detect Pine Script version"""
        if '//@version=5' in code:
            return 5
        elif '//@version=4' in code:
            return 4
        elif '//@version=3' in code:
            return 3
        else:
            return 2  # Legacy

    def _find_inputs(self, code: str) -> list:
        """Find input parameters"""
        inputs = []

        # Match input() functions
        input_pattern = r'(\w+)\s*=\s*input(?:\.\w+)?\s*\((.*?)\)'
        matches = re.finditer(input_pattern, code, re.DOTALL)

        for match in matches:
            var_name = match.group(1)
            args = match.group(2)

            # Extract default value
            default_match = re.search(r'(?:defval\s*=\s*|^)(\d+\.?\d*)', args)
            default_value = default_match.group(1) if default_match else None

            inputs.append({
                'name': var_name,
                'default': default_value
            })

        return inputs

    def _find_calculations(self, code: str) -> list:
        """Find main calculation lines"""
        calculations = []

        # Look for common Pine Script functions
        calc_functions = [
            'sma', 'ema', 'rma', 'wma', 'vwma',
            'highest', 'lowest', 'stoch', 'rsi',
            'cci', 'macd', 'atr', 'tr', 'bb',
            'linreg', 'correlation', 'dev'
        ]

        for func in calc_functions:
            if func + '(' in code:
                calculations.append(func)

        return calculations

    def _extract_metadata(self, code: str) -> Dict:
        """Extract metadata from Pine Script"""
        metadata = {}

        # Extract title
        title_match = re.search(r'title\s*=\s*["\']([^"\']+)["\']', code)
        if title_match:
            metadata['title'] = title_match.group(1)

        # Extract short title
        short_match = re.search(r'shorttitle\s*=\s*["\']([^"\']+)["\']', code)
        if short_match:
            metadata['short_title'] = short_match.group(1)

        # Extract overlay
        overlay_match = re.search(r'overlay\s*=\s*(true|false)', code)
        if overlay_match:
            metadata['overlay'] = overlay_match.group(1) == 'true'

        # Create description
        if 'title' in metadata:
            metadata['description'] = metadata['title']
        elif 'short_title' in metadata:
            metadata['description'] = metadata['short_title']
        else:
            metadata['description'] = 'Pine Script Indicator'

        return metadata

    async def _generate_python_code(
        self,
        pine_script: str,
        analysis: Dict,
        metadata: Dict,
        custom_name: Optional[str]
    ) -> str:
        """
        Generate Python code using GPT-4

        This is a placeholder for AI-powered conversion.
        In production, this would call OpenAI GPT-4 API.
        """

        # TODO: Implement actual GPT-4 API call
        # For now, return a template-based conversion

        return self._template_based_conversion(
            pine_script=pine_script,
            analysis=analysis,
            metadata=metadata,
            custom_name=custom_name
        )

    def _template_based_conversion(
        self,
        pine_script: str,
        analysis: Dict,
        metadata: Dict,
        custom_name: Optional[str]
    ) -> str:
        """
        Template-based conversion (fallback method)

        Provides basic conversion for common patterns.
        """

        # Generate function name
        if custom_name:
            func_name = f"calculate_{custom_name.lower().replace(' ', '_')}"
        elif 'title' in metadata:
            func_name = f"calculate_{metadata['title'].lower().replace(' ', '_').replace('-', '_')}"
        else:
            func_name = "calculate_custom_indicator"

        # Build parameter list
        params = ['df: pd.DataFrame']
        for inp in analysis['inputs']:
            param_name = inp['name']
            default_val = inp['default'] if inp['default'] else '14'
            params.append(f"{param_name}: int = {default_val}")

        params_str = ', '.join(params)

        # Generate docstring
        description = metadata.get('description', 'Custom indicator from Pine Script')

        # Build code template
        code_template = f'''def {func_name}({params_str}) -> pd.Series:
    """
    {description}

    Converted from Pine Script

    Args:
        df: DataFrame with OHLCV data
'''

        # Add parameter documentation
        for inp in analysis['inputs']:
            code_template += f'        {inp["name"]}: Parameter from Pine Script\n'

        code_template += f'''
    Returns:
        pandas Series with indicator values
    """
    high = df['high']
    low = df['low']
    close = df['close']

    # TODO: Implement conversion logic
    # This is a template - actual conversion requires AI or manual implementation

    # Common Pine Script pattern conversions:
    # Pine: sma(close, length) → Python: close.rolling(window=length).mean()
    # Pine: ema(close, length) → Python: close.ewm(span=length, adjust=False).mean()
    # Pine: highest(high, length) → Python: high.rolling(window=length).max()
    # Pine: lowest(low, length) → Python: low.rolling(window=length).min()

    # Placeholder: Return simple moving average
    result = close.rolling(window={analysis['inputs'][0]['default'] if analysis['inputs'] else 14}).mean()

    return result
'''

        self.warnings.append(
            "Template-based conversion used. For accurate conversion, "
            "please review and implement the actual Pine Script logic."
        )

        return code_template

    def _validate_python_code(self, code: str) -> Dict:
        """Validate generated Python code"""
        try:
            # Basic syntax check
            compile(code, '<string>', 'exec')

            # Check for required imports
            required_patterns = [
                r'pd\.DataFrame',  # Uses pandas
                r'def\s+\w+\s*\(',  # Has function definition
                r'return\s+',  # Returns something
            ]

            for pattern in required_patterns:
                if not re.search(pattern, code):
                    return {
                        'valid': False,
                        'error': f'Missing required pattern: {pattern}'
                    }

            return {'valid': True, 'error': None}

        except SyntaxError as e:
            return {
                'valid': False,
                'error': f'Syntax error: {str(e)}'
            }

    def _extract_function_name(self, code: str) -> str:
        """Extract function name from Python code"""
        match = re.search(r'def\s+(\w+)\s*\(', code)
        if match:
            return match.group(1)
        return 'unknown_function'

    def _extract_parameters(self, code: str) -> Dict:
        """Extract function parameters"""
        params = {}

        # Find function signature
        sig_match = re.search(r'def\s+\w+\s*\((.*?)\):', code, re.DOTALL)
        if sig_match:
            sig = sig_match.group(1)

            # Parse parameters
            param_pattern = r'(\w+):\s*(\w+(?:\[.*?\])?)\s*(?:=\s*(.+?))?(?:,|$)'
            for match in re.finditer(param_pattern, sig):
                param_name = match.group(1)
                param_type = match.group(2)
                param_default = match.group(3)

                # Skip 'df' parameter
                if param_name == 'df':
                    continue

                params[param_name] = {
                    'type': param_type,
                    'default': param_default.strip() if param_default else None
                }

        return params

    def create_strategy_class(
        self,
        indicator_code: str,
        strategy_name: str,
        entry_conditions: str,
        exit_conditions: Optional[str] = None
    ) -> str:
        """
        Create a complete strategy class using the converted indicator

        Args:
            indicator_code: Converted indicator Python code
            strategy_name: Name for the strategy
            entry_conditions: Entry logic description
            exit_conditions: Exit logic description

        Returns:
            Complete Python strategy class code
        """

        class_name = ''.join(word.capitalize() for word in strategy_name.split('_'))

        strategy_template = f'''class {class_name}Strategy(BaseStrategy):
    """
    {strategy_name.replace('_', ' ').title()} Strategy

    Entry Conditions:
    {entry_conditions}

    Exit Conditions:
    {exit_conditions or 'Use stop-loss and take-profit levels'}
    """

    def __init__(
        self,
        period: int = 14,
        atr_sl_multiplier: float = 1.5,
        atr_tp_multiplier: float = 3.0
    ):
        super().__init__("{strategy_name}")
        self.period = period
        self.atr_sl_multiplier = atr_sl_multiplier
        self.atr_tp_multiplier = atr_tp_multiplier

    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Signal:
        """Generate trading signal"""

        # Calculate indicator
        # {indicator_code.split('def')[1].split('(')[0].strip()} implementation here

        # Generate signal based on conditions
        should_enter = False
        direction = 'LONG'
        confidence = 0.0

        # TODO: Implement entry logic based on indicator

        # Calculate stop-loss and take-profit
        atr = calculate_atr(df, period=14)
        current_atr = atr.iloc[-1]

        stop_loss, take_profit = self.calculate_stop_loss_take_profit(
            entry_price=current_price,
            direction=direction,
            atr=current_atr,
            atr_multiplier_sl=self.atr_sl_multiplier,
            atr_multiplier_tp=self.atr_tp_multiplier
        )

        return Signal(
            should_enter=should_enter,
            direction=direction,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reasoning="{strategy_name} signal"
        )
'''

        return strategy_template


# Singleton instance
_converter_instance = None


def get_pine_converter(api_key: Optional[str] = None) -> PineScriptConverter:
    """Get or create Pine Script converter instance"""
    global _converter_instance

    if _converter_instance is None:
        _converter_instance = PineScriptConverter(api_key)

    return _converter_instance
