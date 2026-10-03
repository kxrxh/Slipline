local M = {}
-- No wheel-generator interception: retain the game's native construction.
M.onExtensionLoaded = function()
  log('I','automaticTyres','Automatic Tyres 0.2.1: stock wheel construction preserved')
end
return M
