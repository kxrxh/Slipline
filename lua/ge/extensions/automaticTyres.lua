local M = {}
-- No wheel-generator interception: retain the game's native construction.
M.onExtensionLoaded = function()
  log('I','automaticTyres','Slipline 0.2.4: stock wheel construction preserved')
end
return M
