function pass = assert_near(actual, expected, tol, name)
    % assert_near - check that actual is within tol of expected
    % Returns true if |actual - expected| < tol, prints FAIL message otherwise
    pass = abs(actual - expected) < tol;
    if ~pass
        fprintf('  FAIL: %s: got %.6g, expected %.6g (tol %.6g)\n', name, actual, expected, tol);
    end
end
