def compile_rules(ir):
    """
    Compiles a list of IR objects into Rule objects.

    Args:
        ir (List[IR]): A list of IR objects to compile.

    Returns:
        List[Rule]: A list of compiled Rule objects.
    """
    rules = []
    for item in ir:
        # Example rule compilation logic
        rule = Rule(condition=item.condition, action=item.action)
        rules.append(rule)
    return rules